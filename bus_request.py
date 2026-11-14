import json
import os
from datetime import datetime, timedelta
from fpdf import FPDF
from fpdf.enums import XPos, YPos

CONFIG_FILE = "config.json"

# Демо-настройки по умолчанию (создаются автоматически в config.json)
DEFAULT_CONFIG = {
    "department_name": "Название подразделения",
    "department_number": "XX-00-00",
    "responsible_name": "Имя Фамилия",
    "position": "Должность",
    "phone": "+7 (000) 000-00-00",
    "default_origin": 'Пункт отправления',
    "default_destination": "Пункт назначения",
    "default_outbound_departure": "08:10",
    "default_travel_hours": 1,
    "default_travel_minutes": 20,
    "default_return_schedule": {
        "1": "11:30",
        "2": "13:20",
        "3": "15:20",
        "4": "17:00",
    },
    "default_fallback_return_time": "17:00",
}


def load_config():
  """Загружает конфигурацию из config.json.

  Если файла нет — создает его с демо-значениями по умолчанию.
  """
  if not os.path.exists(CONFIG_FILE):
    try:
      with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=4)
    except Exception:
      pass
    return DEFAULT_CONFIG

  try:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
      user_config = json.load(f)
      config = DEFAULT_CONFIG.copy()
      config.update(user_config)
      return config
  except Exception:
    return DEFAULT_CONFIG


def save_config(config_data):
  """Сохраняет актуальные настройки в config.json."""
  try:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
      json.dump(config_data, f, ensure_ascii=False, indent=4)
  except Exception:
    pass


class BusRequestPDF(FPDF):
  """Класс для генерации PDF-документа заявки на выделение автобуса."""

  def __init__(self, department_full_name="", *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.department_full_name = department_full_name

  def header(self):
    self.set_font("DejaVu", "B", 15)
    self.cell(
        0,
        8,
        "ЗАЯВКА НА ВЫДЕЛЕНИЕ АВТОБУСА",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
        align="C",
    )

    if self.department_full_name:
      self.set_font("DejaVu", "B", 13)
      self.cell(
          0,
          8,
          self.department_full_name,
          new_x=XPos.LMARGIN,
          new_y=YPos.NEXT,
          align="C",
      )

    self.ln(5)


def generate_bus_request(data, dept_name="", dept_number=""):
  """Генерирует и сохраняет PDF-файл заявки."""
  output_folder = "output"
  fonts_folder = "fonts"

  os.makedirs(output_folder, exist_ok=True)
  os.makedirs(fonts_folder, exist_ok=True)

  full_department = f"{dept_name} {dept_number}".strip()

  departure_datetime = data.get("outbound", {}).get(
      "departure_time", "2026-01-01 00:00"
  )
  date_only = departure_datetime.split(" ")[0].replace(".", "-")

  clean_number = dept_number.replace(" ", "_") if dept_number else "General"
  output_filename = f"Заявка_{clean_number}_от_{date_only}.pdf"
  full_path = os.path.join(output_folder, output_filename)

  pdf = BusRequestPDF(
      department_full_name=full_department,
      orientation="P",
      unit="mm",
      format="A4",
  )

  font_regular = os.path.join(fonts_folder, "DejaVuSans.ttf")
  font_bold = os.path.join(fonts_folder, "DejaVuSans-Bold.ttf")

  if os.path.exists(font_regular) and os.path.exists(font_bold):
    pdf.add_font("DejaVu", "", font_regular)
    pdf.add_font("DejaVu", "B", font_bold)
  else:
    print(
        "⚠️ Предупреждение: Файлы шрифтов DejaVuSans.ttf / DejaVuSans-Bold.ttf не"
        f" найдены в папке '{fonts_folder}'!"
    )

  pdf.add_page()
  pdf.set_auto_page_break(auto=True, margin=15)

  def draw_section(title, section_data):
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")

    pdf.set_font("DejaVu", "", 10)

    from_place = section_data.get("from_where", "")
    to_place = section_data.get("to_where", "")
    auto_route = f"{from_place} -> {to_place}"

    pdf.cell(
        95,
        10,
        f"Время выезда: {section_data.get('departure_time', '')}",
        border=1,
        new_x=XPos.RIGHT,
        new_y=YPos.TOP,
    )
    pdf.cell(
        95,
        10,
        f"Откуда: {from_place}",
        border=1,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    pdf.cell(
        95,
        10,
        f"Время приезда: {section_data.get('arrival_time', '')}",
        border=1,
        new_x=XPos.RIGHT,
        new_y=YPos.TOP,
    )
    pdf.cell(
        95,
        10,
        f"Куда: {to_place}",
        border=1,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    pdf.cell(
        190,
        10,
        f"Маршрут движения: {auto_route}",
        border=1,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    pdf.set_font("DejaVu", "B", 10)
    resp_text = (
        f"Ответственный: {section_data.get('responsible_name', '')} /"
        f" {section_data.get('position', '')} / ТЕЛ."
        f" {section_data.get('phone', '')}"
    )
    pdf.cell(
        190,
        10,
        resp_text,
        border=1,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    pass_text = (
        f"Количество пассажиров — {section_data.get('passengers_count', 0)} чел"
    )
    pdf.cell(
        190,
        10,
        pass_text,
        border=1,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    pdf.ln(10)

  draw_section("ТУДА", data.get("outbound", {}))
  draw_section("ОБРАТНО", data.get("inbound", {}))

  pdf.output(full_path)
  print(f"\n✅ Заявка успешно создана и сохранена по пути: {full_path}")


if __name__ == "__main__":
  config = load_config()

  print("=== ГЕНЕРАТОР ЗАЯВОК НА АВТОБУС ===")

  # 1. Запрос даты поездки
  raw_date = input("Введите дату в формате ДДММГГГГ: ").strip()
  if len(raw_date) == 8 and raw_date.isdigit():
    trip_date = f"{raw_date[:2]}.{raw_date[2:4]}.{raw_date[4:]}"
  else:
    trip_date = raw_date


  # Вспомогательные функции форматирования
  def format_time(t):
    t = t.strip()
    if len(t) == 4 and t.isdigit():
      return f"{t[:2]}:{t[2:]}"
    return t


  def calculate_arrival(date_str, time_str, hours, minutes):
    try:
      full_str = f"{date_str} {time_str}"
      dt = datetime.strptime(full_str, "%d.%m.%Y %H:%M")
      dt_arrival = dt + timedelta(hours=hours, minutes=minutes)
      return dt_arrival.strftime("%d.%m.%Y %H:%M")
    except Exception:
      return f"{date_str} --:--"


  def parse_travel_time(raw_str, default_h, default_m):
    raw_str = raw_str.strip()
    if not raw_str:
      return default_h, default_m
    if ":" in raw_str:
      parts = raw_str.split(":")
      try:
        return int(parts[0]), int(parts[1])
      except ValueError:
        return default_h, default_m
    elif raw_str.isdigit():
      total_mins = int(raw_str)
      return total_mins // 60, total_mins % 60
    return default_h, default_m


  # 2. Выбор режима (стандартный или ручной)
  use_default_input = (
      input("Использовать стандартные настройки? [Enter - да / н - нет]: ")
      .strip()
      .lower()
  )

  # Переменные конфигурации для удобства
  def_dept_name = config.get("department_name", "Учебная группа")
  def_dept_num = config.get("department_number", "XX-00-00")
  def_resp_name = config.get("responsible_name", "Имя Фамилия")
  def_pos = config.get("position", "Староста")
  def_phone = config.get("phone", "+7 (000) 000-00-00")
  def_origin = config.get("default_origin", 'г. Город, ост. "Название"')
  def_dest = config.get("default_destination", "Пункт назначения")
  def_out_dep = config.get("default_outbound_departure", "08:10")
  def_travel_h = config.get("default_travel_hours", 1)
  def_travel_m = config.get("default_travel_minutes", 20)
  return_schedule = config.get(
      "default_return_schedule",
      {"1": "11:30", "2": "13:20", "3": "15:20", "4": "17:00"},
  )
  fallback_return = config.get("default_fallback_return_time", "17:00")

  # === БЛОК СТАНДАРТНОГО СЦЕНАРИЯ ===
  if use_default_input == "":
    department_name = def_dept_name
    department_number = def_dept_num

    outbound_dep_formatted = def_out_dep

    lessons_count = input(
        "Введите количество занятий (1, 2, 3 или 4): "
    ).strip()
    inbound_dep_formatted = return_schedule.get(lessons_count, fallback_return)

    outbound_passengers = input("Введите количество пассажиров (ТУДА): ")
    inbound_passengers = input("Введите количество пассажиров (ОБРАТНО): ")

    origin_place = def_origin
    destination_place = def_dest

    travel_h = def_travel_h
    travel_m = def_travel_m

    resp_name = def_resp_name
    resp_pos = def_pos
    resp_phone = def_phone

  # === БЛОК РУЧНОГО ВВОДА ===
  else:
    print("\n--- РУЧНОЙ ВВОД ПАРАМЕТРОВ ---")

    department_name = (
        input(f"Название подразделения [по умолчанию: {def_dept_name}]: ").strip()
        or def_dept_name
    )
    department_number = (
        input(
            f"Номер подразделения/группы [по умолчанию: {def_dept_num}]: "
        ).strip()
        or def_dept_num
    )

    resp_name = (
        input(f"ФИО ответственного [по умолчанию: {def_resp_name}]: ").strip()
        or def_resp_name
    )
    resp_pos = (
        input(f"Должность ответственного [по умолчанию: {def_pos}]: ").strip()
        or def_pos
    )
    resp_phone = (
        input(f"Телефон ответственного [по умолчанию: {def_phone}]: ").strip()
        or def_phone
    )

    # Сохраняем новые данные в конфигурацию
    config["department_name"] = department_name
    config["department_number"] = department_number
    config["responsible_name"] = resp_name
    config["position"] = resp_pos
    config["phone"] = resp_phone
    save_config(config)

    origin_place = (
        input(f"Пункт отправления [по умолчанию: {def_origin}]: ").strip()
        or def_origin
    )
    destination_place = (
        input(f"Пункт назначения [по умолчанию: {def_dest}]: ").strip()
        or def_dest
    )

    raw_outbound_dep = input("Время выезда ТУДА (ЧЧММ): ")
    outbound_dep_formatted = format_time(raw_outbound_dep)
    outbound_passengers = input("Количество пассажиров ТУДА: ")

    raw_inbound_dep = input("Время выезда ОБРАТНО (ЧЧММ): ")
    inbound_dep_formatted = format_time(raw_inbound_dep)
    inbound_passengers = input("Количество пассажиров ОБРАТНО: ")

    raw_travel = input(
        f"Время в пути (в минутах или ЧЧ:ММ) [по умолчанию: {def_travel_h}ч"
        f" {def_travel_m}мин]: "
    ).strip()
    travel_h, travel_m = parse_travel_time(raw_travel, def_travel_h, def_travel_m)

  # Расчет времени приезда
  outbound_departure_time = f"{trip_date} {outbound_dep_formatted}"
  outbound_arrival_time = calculate_arrival(
      trip_date, outbound_dep_formatted, travel_h, travel_m
  )

  inbound_departure_time = f"{trip_date} {inbound_dep_formatted}"
  inbound_arrival_time = calculate_arrival(
      trip_date, inbound_dep_formatted, travel_h, travel_m
  )

  # Сборка финального словаря данных
  request_data = {
      "outbound": {
          "departure_time": outbound_departure_time,
          "from_where": origin_place,
          "arrival_time": outbound_arrival_time,
          "to_where": destination_place,
          "responsible_name": resp_name,
          "position": resp_pos,
          "phone": resp_phone,
          "passengers_count": outbound_passengers,
      },
      "inbound": {
          "departure_time": inbound_departure_time,
          "from_where": destination_place,
          "arrival_time": inbound_arrival_time,
          "to_where": origin_place,
          "responsible_name": resp_name,
          "position": resp_pos,
          "phone": resp_phone,
          "passengers_count": inbound_passengers,
      },
  }

  generate_bus_request(
      request_data,
      dept_name=department_name,
      dept_number=department_number,
  )