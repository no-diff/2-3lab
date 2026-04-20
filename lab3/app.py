import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import re
from io import StringIO

st.set_page_config(layout="wide")

# ----------------------------
# ЗАВАНТАЖЕННЯ ТА ОЧИЩЕННЯ ДАНИХ
# ----------------------------
@st.cache_data
def load_data():
    import pandas as pd
    import os
    import re
    from io import StringIO

    headers = ['Year', 'Week', 'SMN', 'SMT', 'VCI', 'TCI', 'VHI', 'empty']
    frames = []

    data_path = os.path.join(os.path.dirname(__file__), "../lab2/data")

    for file in os.listdir(data_path):
        if file.endswith(".csv"):
            file_path = os.path.join(data_path, file)

            # читаємо файл
            with open(file_path, 'r') as f:
                text = f.read()

            # прибираємо HTML
            text = re.sub(r'<.*?>', '', text)

            # читаємо як CSV
            df = pd.read_csv(StringIO(text), names=headers)

            # додаємо область
            province_id = int(file.split("_")[1].replace("ID", ""))
            df['area'] = province_id

            frames.append(df)

    # об'єднуємо всі області
    df = pd.concat(frames, ignore_index=True)

    # ----------------------------
    # ОЧИЩЕННЯ (ОДИН РАЗ ДЛЯ ВСІХ ДАНИХ)
    # ----------------------------

    # конвертація в числа
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df['Week'] = pd.to_numeric(df['Week'], errors='coerce')

    for col in ['VCI', 'TCI', 'VHI']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # видаляємо сміття
    df = df.dropna(subset=['Year', 'Week', 'VCI', 'TCI', 'VHI'])

    # прибираємо некоректні значення
    df = df[df['VHI'] != -1]

    # назви областей
    areas = {
        1: "Вінницька", 2: "Волинська", 3: "Дніпропетровська",
        4: "Донецька", 5: "Житомирська", 6: "Закарпатська",
        7: "Запорізька", 8: "Івано-Франківська", 9: "Київська",
        10: "Кіровоградська", 11: "Луганська", 12: "Львівська",
        13: "Миколаївська", 14: "Одеська", 15: "Полтавська",
        16: "Рівненська", 17: "Сумська", 18: "Тернопільська",
        19: "Харківська", 20: "Херсонська", 21: "Хмельницька",
        22: "Черкаська", 23: "Чернівецька", 24: "Чернігівська",
        25: "Крим"
    }

    df['area_name'] = df['area'].map(areas)

    return df


df = load_data()

# ----------------------------
# SIDEBAR
# ----------------------------
st.sidebar.title("Фільтри")

index_type = st.sidebar.selectbox("Індекс", ["VCI", "TCI", "VHI"])

area = st.sidebar.selectbox(
    "Область",
    sorted(df['area_name'].dropna().unique())
)

year_min = int(df['Year'].min())
year_max = int(df['Year'].max())

years = st.sidebar.slider(
    "Роки",
    year_min,
    year_max,
    (year_min, year_max)
)

weeks = st.sidebar.slider(
    "Тижні",
    1,
    52,
    (1, 52)
)

sort_desc = st.sidebar.checkbox("Сортувати за спаданням")

if st.sidebar.button("Reset"):
    st.experimental_rerun()

# ----------------------------
# ФІЛЬТРАЦІЯ
# ----------------------------
filtered = df[
    (df['area_name'] == area) &
    (df['Year'] >= years[0]) &
    (df['Year'] <= years[1]) &
    (df['Week'] >= weeks[0]) &
    (df['Week'] <= weeks[1])
]

filtered = filtered.sort_values(by=index_type, ascending=not sort_desc)

# ----------------------------
# TABS
# ----------------------------
tab1, tab2, tab3 = st.tabs(["Таблиця", "Графік", "Порівняння"])

# ----------------------------
# TAB 1 — TABLE
# ----------------------------
with tab1:
    st.subheader("Дані")
    st.dataframe(filtered[['Year', 'Week', 'area_name', index_type]])

# ----------------------------
# TAB 2 — GRAPH
# ----------------------------
with tab2:
    st.subheader("Часовий ряд")

    if filtered.empty:
        st.warning("Немає даних для відображення")
    else:
        # створюємо нормальну вісь часу
        filtered = filtered.sort_values(by=['Year', 'Week'])
        filtered['time'] = filtered['Year'].astype(str) + "-W" + filtered['Week'].astype(str)

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(
            range(len(filtered)),
            filtered[index_type],
            linewidth=2
        )

        ax.set_title(f"{index_type} для області: {area}", fontsize=14)
        ax.set_xlabel("Час (рік-тиждень)", fontsize=12)
        ax.set_ylabel(index_type, fontsize=12)

        # підпис тіксів (не всі, щоб не було каші)
        step = max(len(filtered) // 10, 1)
        ax.set_xticks(range(0, len(filtered), step))
        ax.set_xticklabels(filtered['time'].iloc[::step], rotation=45)

        ax.grid(True, linestyle='--', alpha=0.5)

        plt.tight_layout()
        st.pyplot(fig)

# ----------------------------
# TAB 3 — COMPARISON
# ----------------------------
with tab3:
    st.subheader("Порівняння областей")

    selected_areas = st.multiselect(
        "Оберіть області",
        df['area_name'].dropna().unique(),
        default=[area]
    )

    comp_df = df[
        (df['area_name'].isin(selected_areas)) &
        (df['Year'] >= years[0]) &
        (df['Year'] <= years[1])
    ]

    if comp_df.empty:
        st.warning("Немає даних для порівняння")
    else:
        fig, ax = plt.subplots(figsize=(10, 5))

        for a in selected_areas:
            temp = comp_df[comp_df['area_name'] == a]
            temp = temp.sort_values(by=['Year', 'Week'])

            # усереднення по тижнях → щоб не було хаосу між роками
            weekly_avg = temp.groupby('Week')[index_type].mean()

            ax.plot(
                weekly_avg.index,
                weekly_avg.values,
                linewidth=2,
                label=a
            )

        ax.set_title(f"Порівняння областей ({index_type})", fontsize=14)
        ax.set_xlabel("Тиждень", fontsize=12)
        ax.set_ylabel(index_type, fontsize=12)

        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.5)

        plt.tight_layout()
        st.pyplot(fig)