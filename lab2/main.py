import urllib.request
from datetime import datetime
import pandas as pd
import os

DATA_DIR = "data"

# створення папки для даних
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# -------------------------
# назви областей
# -------------------------
AREA_NAMES = {
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

# -------------------------
# завантаження даних
# -------------------------
def download_vhi(province_id):
    url = f'https://www.star.nesdis.noaa.gov/smcd/emb/vci/VH/get_TS_admin.php?country=UKR&provinceID={province_id}&year1=1981&year2=2024&type=Mean'

    try:
        response = urllib.request.urlopen(url)
        text = response.read()

        timestamp = datetime.now().strftime("%d%m%Y%H%M%S")
        filename = f"{DATA_DIR}/NOAA_ID{province_id}_{timestamp}.csv"

        with open(filename, 'wb') as f:
            f.write(text)

        print(f"[OK] Область {province_id} завантажена")

    except Exception as e:
        print(f"[ERROR] Область {province_id}: {e}")


def download_all():
    print("\n=== Завантаження даних ===")
    for i in range(1, 26):
        download_vhi(i)


# -------------------------
# завантаження в DataFrame
# -------------------------
def load_data():
    print("\n=== Завантаження в DataFrame ===")

    headers = ['Year', 'Week', 'SMN', 'SMT', 'VCI', 'TCI', 'VHI', 'empty']
    all_data = pd.DataFrame()

    for file in os.listdir(DATA_DIR):
        if file.endswith(".csv"):
            path = os.path.join(DATA_DIR, file)

            try:
                df = pd.read_csv(path, header=1, names=headers)

                # ПРИВОДИМО ДО ЧИСЕЛ
                df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
                df['Week'] = pd.to_numeric(df['Week'], errors='coerce')
                df['VHI'] = pd.to_numeric(df['VHI'], errors='coerce')

                # ВИДАЛЯЄМО ВСЕ СМІТТЯ
                df = df.dropna(subset=['Year', 'Week', 'VHI'])

                # ПРИВОДИМО ДО int
                df['Year'] = df['Year'].astype(int)
                df['Week'] = df['Week'].astype(int)

                # видаляємо -1
                df = df[df['VHI'] != -1]

                # область
                area_id = int(file.split('_')[1].replace('ID', ''))
                df['area'] = area_id

                all_data = pd.concat([all_data, df], ignore_index=True)

            except Exception as e:
                print(f"[ERROR] файл {file}: {e}")

    # назви областей
    all_data['area_name'] = all_data['area'].map(AREA_NAMES)

    print("[OK] Дані завантажені у DataFrame")
    return all_data
# -------------------------
# АНАЛІТИКА
# -------------------------

# VHI за рік
def vhi_for_year(df, area, year):
    print(f"\n=== VHI для області {AREA_NAMES[area]} за {year} рік ===")

    result = df[(df['area'] == area) & (df['Year'] == year)]

    if result.empty:
        print("Дані відсутні для цього року")
    else:
        print(result[['Week', 'VHI']])


# статистика
def stats(df, area, year):
    print(f"\n=== Статистика ({AREA_NAMES[area]}, {year}) ===")

    subset = df[(df['area'] == area) & (df['Year'] == year)]

    if subset.empty:
        print("Дані відсутні")
        return

    print("Min:", subset['VHI'].min())
    print("Max:", subset['VHI'].max())
    print("Mean:", round(subset['VHI'].mean(), 2))
    print("Median:", subset['VHI'].median())


# діапазон років
def range_vhi(df, areas, start, end):
    print(f"\n=== VHI за період {start}-{end} ===")

    result = df[
        (df['area'].isin(areas)) &
        (df['Year'] >= start) &
        (df['Year'] <= end)
    ]

    print(result[['Year', 'area_name', 'VHI']])


# аналіз посух
def drought_analysis(df):
    print("\n=== АНАЛІЗ ПОСУХ ===")

    drought = df[df['VHI'] <= 15]

    for year in sorted(df['Year'].unique()):
        subset = drought[drought['Year'] == year]

        unique_areas = subset['area'].unique()

        if len(unique_areas) >= 5:
            names = [AREA_NAMES[a] for a in unique_areas]

            print(f"\nРік {year}")
            print("Області:", ", ".join(names))
            print("Кількість:", len(names))


# -------------------------
# MAIN
# -------------------------
def main():
    download_all()

    df = load_data()

    print("\n=== АНАЛІЗ ДАНИХ ===")

    vhi_for_year(df, 1, 2000)
    stats(df, 1, 2000)
    range_vhi(df, [1, 2, 3], 2000, 2005)
    drought_analysis(df)


if __name__ == "__main__":
    main()