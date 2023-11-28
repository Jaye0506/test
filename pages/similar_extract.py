import streamlit as st
import zipfile
import pandas as pd
from io import BytesIO
from collections import defaultdict
import re

def save_upload_file(uploaded_file):
    all_dataframes = []  # 用来存储所有的DataFrame列表
    if uploaded_file.name.endswith('.zip'):
        # 使用BytesIO读取上传的ZIP文件
        bytes_data = uploaded_file.read()
        zip_stream = BytesIO(bytes_data)

        with zipfile.ZipFile(zip_stream, 'r') as zipped_file:
            # 获取压缩包内所有文件的列表
            zipped_file_namelist = zipped_file.namelist()
            excel_files = [f for f in zipped_file_namelist if f.endswith('.xlsx')]

            for excel_file_name in excel_files:
                with zipped_file.open(excel_file_name) as excel_file:
                    # 读取Excel文件中的每个工作表
                    xls = pd.ExcelFile(excel_file)
                    for sheet_name in xls.sheet_names:
                        # 读取工作表内容到DataFrame
                        df = pd.read_excel(excel_file, sheet_name=sheet_name)
                        # 新增一列来表示这个DataFrame来自于哪个文件的哪个工作表
                        df['Source'] = f"{excel_file_name} || {sheet_name}"
                        # 将读取的DataFrame添加到列表中
                        all_dataframes.append(df)

        # 合并所有DataFrame成一个单一的DataFrame
        merged_dataframe = pd.concat(all_dataframes, ignore_index=True)
        return merged_dataframe

def get_patterns():
    patterns = {
        'p1':r'\{.+?\}',
        'p2':r'\d+', 
        'p3':r'[零一二三四五六七八九十百千万亿]+',
        'p4':r'<[^>]+>',
        'p5':r'\[[^\]]+\]'
    }
    return patterns

def extract_similar_text(df, source_column:str, pattern_names:list=['p1','p2','p3','p4','p5']):
    patterns = get_patterns()

    combined_patterns = '|'.join([patterns[name] for name in pattern_names if name in patterns])
    df['Replaced_Text'] = df[source_column].str.replace(combined_patterns, 'X', regex=True)

    df['Matched_Patterns'] = ''
    for name in pattern_names:
        if name in patterns:
            pattern = patterns[name]
            # df['Matched_Patterns'] += df[source_column].str.contains(pattern).replace({True: patterns[name] + ' ', False: ''})
            df['Matched_Patterns'] = df.apply(lambda x: pattern if x['Matched_Patterns'] == '' and pd.notnull(x[source_column]) and bool(re.search(pattern, x[source_column])) else x['Matched_Patterns'], axis=1)
    # 对于没有匹配模式的文本，将 'Matched_Patterns' 列填充为 '100%'
    df['Matched_Patterns'] = df['Matched_Patterns'].replace('', '100%')

    # 将处理后的文本进行分组，以找出重复出现的模式
    pattern_dict = defaultdict(list)
    for original_text, replaced_text in zip(df[source_column], df['Replaced_Text']):
        pattern_dict[replaced_text].append(original_text)

    similar_text_total = 0
    similar_text_data = pd.DataFrame()
    for replaced_text, original_texts in pattern_dict.items():
        if len(original_texts) > 1:
            # 从第二次出现的文本开始计数
            similar_text_total += (len(original_texts) - 1) * len(replaced_text)
            matching_rows = df[df[source_column].isin(original_texts)]
            # print(f"{replaced_text}:{original_texts}")
            # 将找到的行添加到新的 DataFrame 中
            similar_text_data = pd.concat([similar_text_data, matching_rows], ignore_index=True)

    # 计算同质化文本的总字数
    characters_total = df[source_column].str.len().sum()
    # 计算同质化文本率
    similar_text_rate = round((similar_text_total / characters_total) * 100, 2)

    print(f"同质化文本字数:{similar_text_total}\n原文列总字数:{characters_total}\n同质化文本率:{similar_text_rate}%", )
    return similar_text_data, characters_total, similar_text_total, similar_text_rate


# 设置页面标题
st.title('表格同质化文本抽取')

# 创建一个文件上传器
uploaded_file = st.file_uploader("选择ZIP文件", type="zip")
if uploaded_file:
    merged_dataframe = save_upload_file(uploaded_file)
    # 显示结果
    st.write("合并总数据：")
    st.write(merged_dataframe)
    if not merged_dataframe.empty:
        col1, col2, col3 = st.columns(3)
        column_name = st.selectbox('请选择抽取同质化的文本列', merged_dataframe.columns)
        patterns = get_patterns()
        explanations = {
            'p1': "匹配大括号内的内容",
            'p2': "匹配数字",
            'p3': "匹配中文数字",
            'p4': "匹配尖括号内的HTML标签",
            'p5': "匹配方括号内的内容"
        }
        df = pd.DataFrame(list(patterns.items()), columns=['Pattern', 'Regex'])
        df['Explanation'] = df['Pattern'].map(explanations)
        pattern_names = st.multiselect('选择您需要匹配的模式', explanations.keys(), default=explanations.keys())
        st.table(df)
        button = st.button('抽取文本')
        if button:
            similar_text_data, characters_total, similar_text_total, similar_text_rate = extract_similar_text(merged_dataframe, column_name, pattern_names)
            st.write("原文列总字数：", characters_total)
            st.write("同质化文本字数：", similar_text_total)
            st.write(f"同质化文本率：{similar_text_rate}%")
            st.write(similar_text_data)
        
