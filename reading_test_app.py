import pandas as pd

def create_dict_from_excel(file_path):
    # Excelファイルを読み込む
    df = pd.read_excel(file_path)

    # 辞書のリストを作成
    list_of_dicts = [
        {
            "id": int(row["ID"]),
            "title": row["タイトル"],
            "content": row["内容"]
        }
        for _, row in df.iterrows()
    ]

    return list_of_dicts

# この関数を使用して、ファイルを読み込みます。
file_path = './questions.xlsx'  # 実際のファイルパスに置き換えてください
dict_list = create_dict_from_excel(file_path)
print(dict_list)
