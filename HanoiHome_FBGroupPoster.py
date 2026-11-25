import os
import sys
import time
import random
import threading
import subprocess
import queue
import csv
import io
import re
import json
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import pyperclip
from playwright.sync_api import sync_playwright

def find_chrome_executable():
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return "chrome"

# ==============================================================================
# CẤU HÌNH MẶC ĐỊNH CHO HANOI HOME - FACEBOOK GROUPS AUTO POSTER (V6 - PYTHON 3.15 FIX)
# ==============================================================================
SHEET_ID = "1r-q30-q25bgyVDYeBX7rQ9hd8KnhC0hwh_PnQyQ5WC8"
GID = "1547559065"
DEFAULT_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

DEFAULT_REPORT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fVq7q7RB6qGI5PR1-8X24bP5EOqwAX52wcpeigb4gcw/edit?gid=0#gid=0"

_LEGACY_DATA_DIR = Path(r"E:\Cho Thuê Chung Cư")
APP_BASE_DIR = Path(__file__).resolve().parent
DATA_BASE_DIR = _LEGACY_DATA_DIR if _LEGACY_DATA_DIR.exists() else (APP_BASE_DIR / "app_data")

_legacy_img_dir = _LEGACY_DATA_DIR / "680 Tu Hoa"
DEFAULT_IMAGE_DIR = str(_legacy_img_dir if _legacy_img_dir.exists() else APP_BASE_DIR)
FB_CACHE_DIR = str(DATA_BASE_DIR / "fb_cache_data")
FB_CHROME_PROFILE_DIR = str(DATA_BASE_DIR / "fb_chrome_profile")
os.makedirs(FB_CACHE_DIR, exist_ok=True)
os.makedirs(FB_CHROME_PROFILE_DIR, exist_ok=True)

CLEAN_GROUPS_FILE = Path(FB_CACHE_DIR) / "instant_approve_groups.json"
JOINED_GROUPS_FILE = Path(FB_CACHE_DIR) / "joined_groups_history.json"

DEFAULT_FB_GROUPS = (
    "https://www.facebook.com/groups/chothuecanhotayho\n"
    "https://www.facebook.com/groups/chothuecanhodichvutayho"
)

DEFAULT_SEARCH_KEYWORDS = "Hanoi Massive, Hanoi Expats, Hanoi Housing, Tay Ho Apartment"

SCHEDULE_SLOTS = ["09:45", "10:45", "11:45", "14:30"]
DEFAULT_MAX_PHOTOS = 7

TEMPLATE_EXPAT_EN = "Expat English (Chuẩn Hanoi Home)"
TEMPLATE_VIETNAMESE = "Tiếng Việt (Môi giới & Khách Việt)"

CUSTOM_ROOM_PHOTOS_FILE = Path(FB_CACHE_DIR) / "custom_room_photos.json"
HIDDEN_ROOMS_FILE = Path(FB_CACHE_DIR) / "hidden_rooms_config.json"

def load_hidden_rooms_config():
    if HIDDEN_ROOMS_FILE.exists():
        try:
            with open(HIDDEN_ROOMS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("hidden_rooms", [])), set(data.get("hidden_buildings", []))
        except Exception:
            return set(), set()
    return set(), set()

def save_hidden_rooms_config(hidden_rooms, hidden_buildings):
    data = {
        "hidden_rooms": sorted(list(hidden_rooms)),
        "hidden_buildings": sorted(list(hidden_buildings)),
    }
    try:
        HIDDEN_ROOMS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HIDDEN_ROOMS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_custom_room_photos():
    if CUSTOM_ROOM_PHOTOS_FILE.exists():
        try:
            with open(CUSTOM_ROOM_PHOTOS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_custom_room_photo(unit, building, photo_dir):
    data = load_custom_room_photos()
    u_key = str(unit).strip().upper()
    b_key = str(building).strip().upper()
    data[f"{u_key}|{b_key}"] = str(photo_dir)
    try:
        CUSTOM_ROOM_PHOTOS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CUSTOM_ROOM_PHOTOS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

ROOM_IMAGE_DIRS = {
    ("402", "157 Nhật Chiêu"): r"E:\Cho Thuê Chung Cư\157 Nhat Chieu\R402 - 157 Nhat Chieu",
    ("501", "Số 2E ngõ 32/12 Tô Ngọc Vân"): r"E:\Cho Thuê Chung Cư\2E - ngách 12-32TNV\501",
    ("702", "Số 2E ngõ 32/12 Tô Ngọc Vân"): r"E:\Cho Thuê Chung Cư\2E - ngách 12-32TNV\702",
    ("201", "Số 2B ngõ 25 Tây Hồ"): r"E:\Cho Thuê Chung Cư\2B-25 Tay Ho\201 - 2B-25 Tay Ho",
    ("301", "Số 2B ngõ 25 Tây Hồ"): r"E:\Cho Thuê Chung Cư\2B-25 Tay Ho\301 - 2B-25 Tay Ho",
    ("402", "Số 2B ngõ 25 Tây Hồ"): r"E:\Cho Thuê Chung Cư\2B-25 Tay Ho\402 - 2B-25 Tay Ho",
    ("501", "Số 2B ngõ 25 Tây Hồ"): r"E:\Cho Thuê Chung Cư\2B-25 Tay Ho\501 - 2B-25 Tay Ho",
    ("201", "No. 2B, alley 25, Tay Ho street"): r"E:\Cho Thuê Chung Cư\2B-25 Tay Ho\201 - 2B-25 Tay Ho",
    ("301", "No. 2B, alley 25, Tay Ho street"): r"E:\Cho Thuê Chung Cư\2B-25 Tay Ho\301 - 2B-25 Tay Ho",
    ("402", "No. 2B, alley 25, Tay Ho street"): r"E:\Cho Thuê Chung Cư\2B-25 Tay Ho\402 - 2B-25 Tay Ho",
    ("501", "No. 2B, alley 25, Tay Ho street"): r"E:\Cho Thuê Chung Cư\2B-25 Tay Ho\501 - 2B-25 Tay Ho",
    ("201", "Hanoi Home 3"): r"E:\Cho Thuê Chung Cư\2B-25 Tay Ho\201 - 2B-25 Tay Ho",
    ("301", "Hanoi Home 3"): r"E:\Cho Thuê Chung Cư\2B-25 Tay Ho\301 - 2B-25 Tay Ho",
    ("402", "Hanoi Home 3"): r"E:\Cho Thuê Chung Cư\2B-25 Tay Ho\402 - 2B-25 Tay Ho",
    ("501", "Hanoi Home 3"): r"E:\Cho Thuê Chung Cư\2B-25 Tay Ho\501 - 2B-25 Tay Ho",
    ("301", "Số 14 ngõ 19 Tô Ngọc Vân"): r"E:\Cho Thuê Chung Cư\14 -19 Tô Ngọc Vân\Room 301",
    ("301", "Hanoi Home 7"): r"E:\Cho Thuê Chung Cư\14 -19 Tô Ngọc Vân\Room 301",
    ("301", "Hanoi home 7"): r"E:\Cho Thuê Chung Cư\14 -19 Tô Ngọc Vân\Room 301",
    ("301", "14 -19 Tô Ngọc Vân"): r"E:\Cho Thuê Chung Cư\14 -19 Tô Ngọc Vân\Room 301",
    ("301", "14 - 19 Tô Ngọc Vân"): r"E:\Cho Thuê Chung Cư\14 -19 Tô Ngọc Vân\Room 301",
    ("301", "No. 14, alley 19, To Ngoc Van street"): r"E:\Cho Thuê Chung Cư\14 -19 Tô Ngọc Vân\Room 301",
    ("4th floor", "Water Front - Số 1 ngõ 32 Tô Ngọc Vân"): r"E:\Cho Thuê Chung Cư\32TNV\Floor4 - 32TNV",
    ("Floor4", "Water Front - Số 1 ngõ 32 Tô Ngọc Vân"): r"E:\Cho Thuê Chung Cư\32TNV\Floor4 - 32TNV",
    ("Floor 4", "Water Front - Số 1 ngõ 32 Tô Ngọc Vân"): r"E:\Cho Thuê Chung Cư\32TNV\Floor4 - 32TNV",
    ("floor4", "Water Front - Số 1 ngõ 32 Tô Ngọc Vân"): r"E:\Cho Thuê Chung Cư\32TNV\Floor4 - 32TNV",
    ("4", "Water Front - Số 1 ngõ 32 Tô Ngọc Vân"): r"E:\Cho Thuê Chung Cư\32TNV\Floor4 - 32TNV",
    ("5th floor", "Water Front - Số 1 ngõ 32 Tô Ngọc Vân"): r"E:\Cho Thuê Chung Cư\32TNV\Floor5 - 32TNV",
    ("Floor5", "Water Front - Số 1 ngõ 32 Tô Ngọc Vân"): r"E:\Cho Thuê Chung Cư\32TNV\Floor5 - 32TNV",
    ("Floor 5", "Water Front - Số 1 ngõ 32 Tô Ngọc Vân"): r"E:\Cho Thuê Chung Cư\32TNV\Floor5 - 32TNV",
    ("floor5", "Water Front - Số 1 ngõ 32 Tô Ngọc Vân"): r"E:\Cho Thuê Chung Cư\32TNV\Floor5 - 32TNV",
    ("5", "Water Front - Số 1 ngõ 32 Tô Ngọc Vân"): r"E:\Cho Thuê Chung Cư\32TNV\Floor5 - 32TNV",
}

BUILDING_IMAGE_DIRS = {
    "157 Nhật Chiêu": r"E:\Cho Thuê Chung Cư\157 Nhat Chieu",
    "Số 6 ngõ 80 Từ Hoa": r"E:\Cho Thuê Chung Cư\680 Tu Hoa",
    "Số 2B ngõ 25 Tây Hồ": r"E:\Cho Thuê Chung Cư\2B-25 Tay Ho",
    "2B-25 Tay Ho": r"E:\Cho Thuê Chung Cư\2B-25 Tay Ho",
    "2B-25": r"E:\Cho Thuê Chung Cư\2B-25 Tay Ho",
    "Hanoi Home 3": r"E:\Cho Thuê Chung Cư\2B-25 Tay Ho",
    "No. 2B, alley 25, Tay Ho street": r"E:\Cho Thuê Chung Cư\2B-25 Tay Ho",
    "Số 2E ngõ 32/12 Tô Ngọc Vân": r"E:\Cho Thuê Chung Cư\2E - ngách 12-32TNV",
    "Số 14 ngõ 19 Tô Ngọc Vân": r"E:\Cho Thuê Chung Cư\14 -19 Tô Ngọc Vân",
    "14 -19 Tô Ngọc Vân": r"E:\Cho Thuê Chung Cư\14 -19 Tô Ngọc Vân",
    "14 - 19 Tô Ngọc Vân": r"E:\Cho Thuê Chung Cư\14 -19 Tô Ngọc Vân",
    "Hanoi Home 7": r"E:\Cho Thuê Chung Cư\14 -19 Tô Ngọc Vân",
    "No. 14, alley 19, To Ngoc Van street": r"E:\Cho Thuê Chung Cư\14 -19 Tô Ngọc Vân",
    "Water Front - Số 1 ngõ 32 Tô Ngọc Vân": r"E:\Cho Thuê Chung Cư\32TNV",
    "Số 1 ngõ 32 Tô Ngọc Vân": r"E:\Cho Thuê Chung Cư\32TNV",
    "32TNV": r"E:\Cho Thuê Chung Cư\32TNV",
}


def normalize_building_address(building_header):
    bld_upper = building_header.upper()
    if "157 NHẬT CHIÊU" in bld_upper or "157 NHAT CHIEU" in bld_upper:
        return "157 Nhật Chiêu"
    if "HANOI HOME 6" in bld_upper or "80 TỪ HOA" in bld_upper or "80 TU HOA" in bld_upper or "LUMI TU HOA" in bld_upper:
        return "Số 6 ngõ 80 Từ Hoa"
    if (
        "HANOI HOME 3" in bld_upper
        or "25 TÂY HỒ" in bld_upper
        or "25 TAY HO" in bld_upper
        or "2B-25" in bld_upper
        or "2B/25" in bld_upper
        or ("2B" in bld_upper and ("25" in bld_upper or "TÂY HỒ" in bld_upper or "TAY HO" in bld_upper))
    ):
        return "Số 2B ngõ 25 Tây Hồ"
    if "HANOI HOME 10" in bld_upper or "32/12 TÔ NGỌC VÂN" in bld_upper or "32/12 TO NGOC VAN" in bld_upper or "12-32TNV" in bld_upper:
        return "Số 2E ngõ 32/12 Tô Ngọc Vân"
    if (
        "HANOI HOME 7" in bld_upper
        or "14, ALLEY 19" in bld_upper
        or "14 ALLEY 19" in bld_upper
        or "14/19 TÔ NGỌC VÂN" in bld_upper
        or "14/19 TO NGOC VAN" in bld_upper
        or "14 -19 TÔ NGỌC VÂN" in bld_upper
        or "14 - 19 TÔ NGỌC VÂN" in bld_upper
        or "14 -19 TO NGOC VAN" in bld_upper
        or "14 - 19 TO NGOC VAN" in bld_upper
        or ("14" in bld_upper and "19" in bld_upper and ("TÔ NGỌC VÂN" in bld_upper or "TO NGOC VAN" in bld_upper))
    ):
        return "Số 14 ngõ 19 Tô Ngọc Vân"
    if (
        "HANOI HOME 4" in bld_upper
        or "14/11/5" in bld_upper
        or ("14/11" in bld_upper and ("TÔ NGỌC VÂN" in bld_upper or "TO NGOC VAN" in bld_upper))
    ):
        return "Số 14/11/5 Tô Ngọc Vân"
    if (
        "WATER FRONT" in bld_upper
        or "WATERFRONT" in bld_upper
        or "HANOI HOME 9" in bld_upper
        or "1 NGÕ 32 TÔ NGỌC VÂN" in bld_upper
        or "1 NGO 32 TO NGOC VAN" in bld_upper
        or "1/32 TÔ NGỌC VÂN" in bld_upper
        or "1/32 TO NGOC VAN" in bld_upper
        or "32TNV" in bld_upper
        or ("32 TÔ NGỌC VÂN" in bld_upper and "32/12" not in bld_upper)
        or ("32 TO NGOC VAN" in bld_upper and "32/12" not in bld_upper)
    ):
        return "Water Front - Số 1 ngõ 32 Tô Ngọc Vân"
    if "145 ÂU CƠ" in bld_upper or "145 AU CO" in bld_upper or "SOLALA NEST" in bld_upper:
        return "Số 6 ngõ 145 Âu Cơ"
    if "63 TRẦN QUỐC VƯỢNG" in bld_upper or "63 TRAN QUOC VUONG" in bld_upper:
        return "63 Trần Quốc Vượng"
    return " ".join(building_header.split())


def format_building_english(building_addr):
    b = building_addr.strip()
    mapping = {
        "157 Nhật Chiêu": "157 Nhat Chieu, West Lake",
        "Số 6 ngõ 80 Từ Hoa": "No. 6, Alley 80 Tu Hoa, West Lake",
        "Số 2B ngõ 25 Tây Hồ": "No. 2B, Alley 25 Tay Ho, West Lake",
        "Số 2E ngõ 32/12 Tô Ngọc Vân": "No. 2E, Alley 32/12 To Ngoc Van, Tay Ho",
        "Số 14 ngõ 19 Tô Ngọc Vân": "No. 14, Alley 19 To Ngoc Van, Tay Ho",
        "Water Front - Số 1 ngõ 32 Tô Ngọc Vân": "Water Front - No. 1, Alley 32 To Ngoc Van, Tay Ho",
        "Số 6 ngõ 145 Âu Cơ": "No. 6, Alley 145 Au Co, Tay Ho",
        "63 Trần Quốc Vượng": "63 Tran Quoc Vuong, Cau Giay",
    }
    return mapping.get(b, f"{b}, West Lake, Hanoi")


def format_report_building_short(building_addr):
    b = building_addr.strip()
    mapping = {
        "Số 6 ngõ 80 Từ Hoa": "680 Từ Hoa",
        "Số 14 ngõ 19 Tô Ngọc Vân": "14/19 Tô Ngọc Vân",
        "Số 2E ngõ 32/12 Tô Ngọc Vân": "32/12 Tô Ngọc Vân",
        "Số 2B ngõ 25 Tây Hồ": "2B/25 Tây Hồ",
        "Water Front - Số 1 ngõ 32 Tô Ngọc Vân": "32 TNV",
        "Số 6 ngõ 145 Âu Cơ": "6/145 Âu Cơ",
    }
    return mapping.get(b, b)


def resolve_room_image_dir(unit_id, building_name="", fallback_root=None):
    u = str(unit_id).strip()
    bld = str(building_name).strip()
    u_up = u.upper()
    bld_up = bld.upper()

    # 0. Ưu tiên cao nhất: Thư mục ảnh do người dùng tự gán tay cho căn này
    custom_map = load_custom_room_photos()
    for k, p_str in custom_map.items():
        if "|" in k:
            c_u, c_b = k.split("|", 1)
            if c_u == u_up and (not bld_up or c_b in bld_up or bld_up in c_b):
                p = Path(p_str)
                if p.exists():
                    return p

    for (r_unit, r_bld), path_str in ROOM_IMAGE_DIRS.items():
        if u.lower() == str(r_unit).strip().lower():
            if not bld or (r_bld.lower() in bld.lower() or bld.lower() in r_bld.lower()):
                p = Path(path_str)
                if p.exists():
                    return p

    u_digits = re.findall(r"\d+", u)
    u_num = u_digits[0] if u_digits else ""

    if u_num:
        for (r_unit, r_bld), path_str in ROOM_IMAGE_DIRS.items():
            r_digits = re.findall(r"\d+", str(r_unit))
            if r_digits and r_digits[0] == u_num:
                if not bld or (r_bld.lower() in bld.lower() or bld.lower() in r_bld.lower()):
                    p = Path(path_str)
                    if p.exists():
                        return p

    matched_building = False
    for bld_key, root_item in BUILDING_IMAGE_DIRS.items():
        if bld and (bld_key.lower() in bld.lower() or bld.lower() in bld_key.lower()):
            matched_building = True
            root_paths = [root_item] if isinstance(root_item, (str, Path)) else root_item
            for r_str in root_paths:
                root_p = Path(r_str)
                if root_p.exists():
                    for item in root_p.iterdir():
                        if not item.is_dir():
                            continue
                        item_name_up = item.name.strip().upper()
                        item_clean = item_name_up.replace(" ", "").replace("-", "").replace("_", "")
                        u_clean = u.upper().replace(" ", "")
                        if (
                            item_name_up == u.upper()
                            or f"R{u.upper()}" in item_name_up
                            or f"ROOM{u_clean}" in item_clean
                            or f"ROOM {u.upper()}" in item_name_up
                            or f" {u.upper()} " in f" {item_name_up} "
                            or f"{u.upper()} " in item_name_up
                            or f"-{u.upper()}" in item_name_up
                        ):
                            return item
                        if u_num:
                            if (
                                f"FLOOR{u_num}" in item_name_up.replace(" ", "")
                                or f"TANG{u_num}" in item_name_up.replace(" ", "")
                                or f"{u_num}TH" in item_name_up
                                or f"{u_num}ND" in item_name_up
                                or f"{u_num}RD" in item_name_up
                                or f"{u_num}ST" in item_name_up
                            ):
                                return item

    if fallback_root and not matched_building:
        fb_path = Path(fallback_root)
        if fb_path.exists():
            if u.lower() in fb_path.name.lower() or f"R{u}" in fb_path.name.upper() or fb_path.name.strip().upper() == u.upper():
                return fb_path
            for item in fb_path.iterdir():
                if item.is_dir():
                    item_name_up = item.name.strip().upper()
                    item_clean = item_name_up.replace(" ", "").replace("-", "").replace("_", "")
                    u_clean = u.upper().replace(" ", "")
                    if (
                        item_name_up == u.upper()
                        or f"R{u.upper()}" in item_name_up
                        or f"ROOM{u_clean}" in item_clean
                        or f"ROOM {u.upper()}" in item_name_up
                        or f" {u.upper()} " in f" {item_name_up} "
                        or u.lower() in item.name.lower()
                    ):
                        return item
                    if u_num and f"FLOOR{u_num}" in item_name_up.replace(" ", ""):
                        return item

    return None


def get_photo_category(path_or_name):
    stem = Path(path_or_name).stem.lower()
    norm = "".join(c for c in unicodedata.normalize("NFD", stem) if unicodedata.category(c) != "Mn")
    norm_clean = re.sub(r"[-_.]+", " ", norm)

    if any(k in norm for k in ["livingroom", "living", "khach"]):
        return 1
    if any(k in norm for k in ["kitchen", "bep", "island", "dining"]):
        return 2
    if any(k in norm for k in ["bedroom", "ngu"]) or re.search(r"\bbed\b", norm_clean):
        return 3
    if any(k in norm for k in ["balcony", "ban cong", "view", "terrace", "logia", "garage"]):
        return 4
    if any(k in norm for k in ["bathroom", "batroom", "bath", "wc", "toilet", "tam", "ve sinh"]):
        return 5
    return 6


def photo_sub_sort_key(path_or_name):
    stem = Path(path_or_name).stem.lower()
    norm = "".join(c for c in unicodedata.normalize("NFD", stem) if unicodedata.category(c) != "Mn")
    digits = re.findall(r"\d+", norm)
    num = int(digits[0]) if digits else 0
    return (num, norm)


def photo_sort_key(path_or_name):
    return (get_photo_category(path_or_name), photo_sub_sort_key(path_or_name))


def select_and_sort_photos(image_files, max_photos=DEFAULT_MAX_PHOTOS):
    if not image_files:
        return []

    grouped = {}
    for p in image_files:
        cat = get_photo_category(p)
        grouped.setdefault(cat, []).append(p)

    for cat in grouped:
        grouped[cat].sort(key=photo_sub_sort_key)

    if not max_photos or len(image_files) <= max_photos:
        return sorted(image_files, key=photo_sort_key)

    selected = []
    for cat in [1, 2, 3, 4, 5, 6]:
        if cat in grouped and grouped[cat] and len(selected) < max_photos:
            selected.append(grouped[cat].pop(0))

    fill_order = [1, 3, 2, 4, 6, 5]
    while len(selected) < max_photos:
        added = False
        for cat in fill_order:
            if cat in grouped and grouped[cat] and len(selected) < max_photos:
                selected.append(grouped[cat].pop(0))
                added = True
                break
        if not added:
            break

    return sorted(selected, key=photo_sort_key)


def normalize_area_text(area_raw, desc_raw=""):
    a = str(area_raw or "").strip()
    if not a:
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:m2|m²|sqm)", str(desc_raw), re.IGNORECASE)
        if m:
            a = m.group(1)
    if not a:
        return ""
    digits = re.findall(r"\d+(?:[.,]\d+)?", a)
    if digits:
        return f"{digits[0]}m²"
    return a


def build_expat_english_message(room, spin=False):
    unit = str(room.get("unit", "")).strip()
    building = str(room.get("building", "")).strip()
    building_en = format_building_english(building)
    desc = str(room.get("desc", "")).strip()
    area_str = normalize_area_text(room.get("area", ""), desc)
    so_ngu = str(room.get("so_ngu", "1")).strip()
    so_tam = str(room.get("so_tam", "1")).strip()
    price_vnd = str(room.get("price_vnd", room.get("price", ""))).strip()
    price_usd = str(room.get("price_usd", "")).strip()

    usd_clean = re.sub(r"(?i)usd|\$", "", price_usd).strip()
    vnd_clean = re.sub(r"(?i)\s*vnd", "", price_vnd).strip()

    price_line = ""
    if usd_clean and vnd_clean:
        price_line = f"💰 Rental Price: ${usd_clean}/month (~{vnd_clean} VND)"
    elif usd_clean:
        price_line = f"💰 Rental Price: ${usd_clean}/month"
    elif vnd_clean:
        price_line = f"💰 Rental Price: {vnd_clean} VND/month"

    is_studio = "studio" in desc.lower()
    if is_studio:
        bedroom_highlight = "🛏️ Bright & cozy Studio layout – Peaceful and comfortable"
        unit_title_type = "STUDIO"
    else:
        br_word = "private bedroom" if so_ngu == "1" else "private bedrooms"
        bedroom_highlight = f"🛏️ {so_ngu} {br_word} & {so_tam} bathroom(s) – Peaceful and comfortable"
        unit_title_type = f"{so_ngu}BR APARTMENT"

    if area_str:
        headline_options = [
            f"SPACIOUS {area_str} {unit_title_type} FOR RENT | WEST LAKE, HANOI",
            f"BRIGHT & SPACIOUS {area_str} {unit_title_type} | WEST LAKE, HANOI",
            f"MODERN {area_str} {unit_title_type} FOR RENT | TAY HO, HANOI",
        ]
    else:
        headline_options = [
            f"SPACIOUS {unit_title_type} FOR RENT | WEST LAKE, HANOI",
            f"COZY & MODERN {unit_title_type} | WEST LAKE, HANOI",
            f"FULLY FURNISHED {unit_title_type} FOR RENT | TAY HO, HANOI",
        ]

    intro_options = [
        "Your Home Away From Home!\nLooking for a comfortable and spacious apartment in Hanoi's popular West Lake area?\nWelcome to Hanoi Home, where convenience meets comfortable everyday living.",
        "Your Home Away From Home!\nSearching for a bright, fully furnished home in the heart of Tay Ho, Hanoi?\nWelcome to Hanoi Home, designed for effortless and relaxing everyday living.",
        "Your Home Away From Home!\nMove-in ready apartment available now in Hanoi's expat-favorite West Lake neighborhood!\nWelcome to Hanoi Home, where modern comfort meets prime convenience.",
    ]

    headline = random.choice(headline_options) if spin else headline_options[0]
    intro = random.choice(intro_options) if spin else intro_options[0]

    highlights = [bedroom_highlight]
    if area_str:
        highlights.append(f"📐 {area_str} – Generous living space")
    if "balcony" in desc.lower() or "ban công" in desc.lower():
        highlights.append("🌿 Private balcony – Great airflow & outdoor relaxation")
    if "lake view" in desc.lower() or "157 nhật chiêu" in building.lower():
        highlights.append("🌊 Direct West Lake view – Unobstructed scenic beauty")
    if "kitchen island" in desc.lower():
        highlights.append("🍳 Modern kitchen with island & full cooking appliances")
    else:
        highlights.append("🍳 Equipped kitchen with essential appliances")

    highlights.extend([
        "🛋️ Fully furnished living room with sofa and TV",
        "🍽️ Dedicated dining area",
        "☀️ Large windows bringing in plenty of natural light",
        "❄️ Air conditioning for year-round comfort",
    ])
    if price_line:
        highlights.append(price_line)

    highlights_block = "\n".join(highlights)

    luxury_note = ""
    if "157 NHẬT CHIÊU" in building.upper() or "157 NHAT CHIEU" in building.upper():
        luxury_note = "\n✨ New Luxury Apartment – Brand-new high-end residence right by West Lake!"

    footer = (
        f"📍 Location: {building_en}\n"
        f"Enjoy easy access to international restaurants, cozy cafés, shops, and the vibrant Tay Ho expat community.{luxury_note}\n"
        f"Perfect for professionals, couples, or anyone looking for a welcoming long-term home.\n\n"
        f"📲 Schedule Your Viewing Today! (Unit {unit})\n"
        f"💬 WhatsApp: Mr. David Nam: +84 09 646 12240 / Mr. Khanh: +84 962 123 985\n"
        f"📍 West Lake, Hanoi\n"
        f"📩 Message us for availability, rental details, and more photos.\n\n"
        f"💙 HANOI HOME – YOUR HOME AWAY FROM HOME\n"
        f"#WestLakeApartment #HanoiExpats #TayHoLiving #ApartmentForRentHanoi #HanoiHome #ExpatHousing"
    )

    msg = f"{headline}\n{intro}\n\n🏠 Apartment Highlights:\n{highlights_block}\n\n{footer}"
    if spin:
        msg += f"\n[Ref: {unit}-{random.randint(1000, 9999)}]"
    return msg


def build_vietnamese_message(room, spin=False):
    unit = str(room.get("unit", "")).strip()
    building = str(room.get("building", "")).strip()
    area_str = normalize_area_text(room.get("area", ""), room.get("desc", ""))
    so_ngu = str(room.get("so_ngu", "1")).strip()
    so_tam = str(room.get("so_tam", "1")).strip()
    price_vnd = str(room.get("price_vnd", room.get("price", ""))).strip()
    price_usd = str(room.get("price_usd", "")).strip()

    price_items = []
    if price_vnd:
        vnd_val = re.sub(r"(?i)\s*vnd", "", price_vnd).strip()
        if vnd_val:
            price_items.append(f"{vnd_val} VND")
    if price_usd:
        usd_val = re.sub(r"(?i)usd|\$", "", price_usd).strip()
        if usd_val:
            price_items.append(f"${usd_val}")

    price_str = f"Giá: {price_items[0]} ({price_items[1]})" if len(price_items) == 2 else (f"Giá: {price_items[0]}" if price_items else "")

    parts = [f"Căn {unit}", building]
    if area_str:
        parts.append(f"DT {area_str}")
    parts.extend([f"{so_ngu} ngủ", f"{so_tam} tắm"])
    if price_str:
        parts.append(price_str)
    parts.append("Đang Trống (Available)")

    core = ", ".join(parts)
    if "157 NHẬT CHIÊU" in building.upper() or "157 NHAT CHIEU" in building.upper():
        core += ". New Luxury Apartment - Căn hộ hạng sang mới view trực tiếp Hồ Tây"

    if not spin:
        return f"🏡 CHO THUÊ CĂN HỘ TÂY HỒ: {core}. LH: 0962.123.985 (Mr. Khánh) / 0964.612.240 (Mr. David Nam)."

    openers = [
        "🏡 CHO THUÊ CĂN HỘ DỊCH VỤ TÂY HỒ:",
        "✨ TRỐNG SẴN CĂN ĐẸP NHẬN NHÀ Ở NGAY:",
        "🔑 CHÍNH CHỦ CHO THUÊ CĂN HỘ FULL ĐỒ:",
        "🏢 CẬP NHẬT PHÒNG TRỐNG MỚI NHẤT HÔM NAY:",
    ]
    closers = [
        "📩 Inbox hoặc liên hệ trực tiếp 0962.123.985 (Mr. Khánh) / 0964.612.240 (Mr. David Nam) để xem nhà thực tế!",
        "🤝 ACE môi giới kết hợp dẫn khách nhiệt tình, hoa hồng chuẩn. LH: 0962.123.985!",
    ]
    return f"{random.choice(openers)}\n{core}\n\n{random.choice(closers)}\n[Mã tin: {unit}-{random.randint(1000, 9999)}]"


def build_post_message(room, template_mode=TEMPLATE_EXPAT_EN, spin=False):
    if template_mode == TEMPLATE_VIETNAMESE:
        return build_vietnamese_message(room, spin=spin)
    return build_expat_english_message(room, spin=spin)


def normalize_group_base_url(url):
    u = url.strip().split("?")[0].rstrip("/")
    m = re.search(r"(https?://(?:www\.|m\.)?facebook\.com/groups/[^/]+)", u)
    if m:
        return m.group(1).replace("m.facebook.com", "www.facebook.com") + "/"
    return url.strip()


class FBGroupPosterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hanoi Home - FB Groups Auto Poster V6 (Đồng Bộ Sheet Báo Cáo & Tự Vào Lại Nhóm)")
        self.root.geometry("1020x910")
        self.root.minsize(920, 800)

        self.is_posting = False
        self.stop_requested = False
        self.auto_schedule_enabled = False
        self.rooms_data = []
        self.log_queue = queue.Queue()
        self.scheduled_posted_today = set()
        self.today_date = datetime.now().strftime("%Y-%m-%d")

        self.clean_groups = self.load_json_list(CLEAN_GROUPS_FILE)
        self.joined_groups = self.load_json_list(JOINED_GROUPS_FILE)
        self.hidden_rooms, self.hidden_buildings = load_hidden_rooms_config()

        self.setup_ui()
        self.refresh_clean_groups_display()
        self.process_log_queue()
        self.start_clock_thread()
        self.root.after(800, self.trigger_check_sheet)

    @staticmethod
    def load_json_list(file_path):
        if file_path.exists():
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data
            except Exception:
                pass
        return []

    @staticmethod
    def save_json_list(file_path, data_list):
        try:
            file_path.write_text(json.dumps(data_list, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        frame_config = ttk.LabelFrame(self.root, text="⚙️ Cấu hình Group FB, Đồng Bộ Sheet Báo Cáo & Tự Động Kiểm Tra Thành Viên", padding=8)
        frame_config.pack(fill="x", padx=12, pady=4)

        ttk.Label(frame_config, text="Từ khóa tìm nhóm:").grid(row=0, column=0, sticky="w", pady=3)
        search_bar_frame = ttk.Frame(frame_config)
        search_bar_frame.grid(row=0, column=1, sticky="ew", pady=3, padx=5)

        self.ent_keywords = ttk.Entry(search_bar_frame, font=("Segoe UI", 9))
        self.ent_keywords.insert(0, DEFAULT_SEARCH_KEYWORDS)
        self.ent_keywords.pack(side="left", fill="x", expand=True)

        ttk.Label(search_bar_frame, text="Tối đa:").pack(side="left", padx=(6, 2))
        self.spn_max_join = ttk.Spinbox(search_bar_frame, from_=1, to=15, width=4)
        self.spn_max_join.set(5)
        self.spn_max_join.pack(side="left", padx=2)

        self.btn_auto_join = ttk.Button(
            search_bar_frame,
            text="🔍 Tìm & Tham gia nhóm",
            command=self.trigger_search_and_join_groups
        )
        self.btn_auto_join.pack(side="left", padx=(4, 4))

        self.btn_pull_from_report = ttk.Button(
            search_bar_frame,
            text="📥 Lấy nhóm đã đăng từ Sheet Báo Cáo",
            command=self.trigger_pull_groups_from_report_sheet
        )
        self.btn_pull_from_report.pack(side="left", padx=(2, 0))

        groups_split = ttk.Frame(frame_config)
        groups_split.grid(row=1, column=0, columnspan=2, sticky="ew", pady=4)
        groups_split.columnconfigure(0, weight=1)
        groups_split.columnconfigure(1, weight=1)

        left_grp = ttk.LabelFrame(groups_split, text="📌 Danh sách Link Group FB sẽ đăng (Mỗi dòng 1 link)", padding=5)
        left_grp.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        self.txt_groups = scrolledtext.ScrolledText(left_grp, height=4, font=("Segoe UI", 9))
        self.txt_groups.insert("1.0", DEFAULT_FB_GROUPS)
        self.txt_groups.pack(fill="both", expand=True)

        kick_opt_bar = ttk.Frame(left_grp)
        kick_opt_bar.pack(fill="x", pady=(3, 0))
        self.chk_auto_rejoin = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            kick_opt_bar,
            text="🔄 Nếu bị kích/chưa vào nhóm: Tự bấm Xin vào lại & thay thế bằng nhóm tương tự",
            variable=self.chk_auto_rejoin
        ).pack(side="left")

        right_grp = ttk.LabelFrame(groups_split, text="✅ Kho Nhóm Đã Phân Loại (🟢 Đăng Ngay / 🟡 Chờ Duyệt)", padding=5)
        right_grp.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        self.txt_clean_groups = scrolledtext.ScrolledText(right_grp, height=4, font=("Segoe UI", 9), bg="#fcfcfc")
        self.txt_clean_groups.pack(fill="both", expand=True)

        clean_btn_bar = ttk.Frame(right_grp)
        clean_btn_bar.pack(fill="x", pady=(3, 0))
        self.lbl_clean_count = ttk.Label(clean_btn_bar, text="Đã lưu: 0 nhóm", foreground="#15803d")
        self.lbl_clean_count.pack(side="left")

        ttk.Button(
            clean_btn_bar,
            text="📋 Nạp Tất Cả",
            command=self.copy_all_groups_to_active
        ).pack(side="right", padx=(2, 0))

        ttk.Button(
            clean_btn_bar,
            text="⬅️ Nạp nhóm ĐĂNG NGAY (🟢)",
            command=self.copy_instant_groups_to_active
        ).pack(side="right", padx=2)

        drive_sync_bar = ttk.Frame(right_grp)
        drive_sync_bar.pack(fill="x", pady=(3, 0))

        self.btn_sync_groups_drive = ttk.Button(
            drive_sync_bar,
            text="☁️ Lưu Kho Nhóm lên Drive",
            command=self.trigger_sync_groups_to_drive
        )
        self.btn_sync_groups_drive.pack(side="left", fill="x", expand=True, padx=(0, 2))

        self.btn_pull_groups_drive = ttk.Button(
            drive_sync_bar,
            text="📥 Tải Kho Nhóm từ Drive",
            command=self.trigger_pull_groups_from_drive
        )
        self.btn_pull_groups_drive.pack(side="right", fill="x", expand=True, padx=(2, 0))

        paths_row = ttk.Frame(frame_config)
        paths_row.grid(row=2, column=0, columnspan=2, sticky="ew", pady=2)
        paths_row.columnconfigure(1, weight=1)
        paths_row.columnconfigure(3, weight=1)

        ttk.Label(paths_row, text="Thư mục ảnh:").grid(row=0, column=0, sticky="w")
        self.ent_folder = ttk.Entry(paths_row)
        self.ent_folder.insert(0, DEFAULT_IMAGE_DIR)
        self.ent_folder.grid(row=0, column=1, sticky="ew", padx=(4, 10))

        ttk.Label(paths_row, text="Sheet Báo Cáo:").grid(row=0, column=2, sticky="w")
        self.ent_report_sheet = ttk.Entry(paths_row)
        self.ent_report_sheet.insert(0, DEFAULT_REPORT_SHEET_URL)
        self.ent_report_sheet.grid(row=0, column=3, sticky="ew", padx=(4, 0))

        ttk.Label(paths_row, text="Sheet Căn Trống:").grid(row=1, column=0, sticky="w", pady=(3, 0))
        self.ent_sheet = ttk.Entry(paths_row)
        self.ent_sheet.insert(0, DEFAULT_SHEET_URL)
        self.ent_sheet.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(4, 0), pady=(3, 0))

        frame_config.columnconfigure(1, weight=1)

        frame_action = ttk.LabelFrame(self.root, text="🚀 Thao tác, Mẫu Quảng Cáo & Điều khiển Đăng Bài", padding=8)
        frame_action.pack(fill="x", padx=12, pady=4)

        btn_row = ttk.Frame(frame_action)
        btn_row.pack(fill="x", pady=2)

        self.btn_open_login = ttk.Button(btn_row, text="🔑 0. Đăng nhập FB & Google", command=self.trigger_open_login_browser)
        self.btn_open_login.pack(side="left", padx=(0, 4))

        self.btn_load_sheet = ttk.Button(btn_row, text="🔄 1. Cập nhật Căn Trống", command=self.trigger_check_sheet)
        self.btn_load_sheet.pack(side="left", padx=3)

        self.btn_post_selected = ttk.Button(btn_row, text="🚀 2. ĐĂNG CĂN ĐÃ CHỌN", command=self.trigger_post_selected)
        self.btn_post_selected.pack(side="left", padx=4)

        self.btn_auto_post_10 = ttk.Button(
            btn_row,
            text="🎯 3. TỰ ĐỘNG ĐĂNG ĐỦ 10 BÀI & BÁO CÁO (AN TOÀN)",
            command=self.trigger_auto_post_10
        )
        self.btn_auto_post_10.pack(side="left", padx=4)

        self.btn_stop_auto = ttk.Button(
            btn_row,
            text="🛑 DỪNG ĐĂNG BÀI",
            command=self.trigger_stop_auto_post,
            state="disabled"
        )
        self.btn_stop_auto.pack(side="left", padx=4)

        self.chk_auto_click_post = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            btn_row,
            text="Tự bấm Đăng",
            variable=self.chk_auto_click_post,
        ).pack(side="left", padx=4)

        self.chk_auto_report = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            btn_row,
            text="📊 Ghi Sheet",
            variable=self.chk_auto_report,
        ).pack(side="left", padx=4)

        self.chk_auto_var = tk.BooleanVar(value=False)
        self.chk_auto = ttk.Checkbutton(
            btn_row,
            text="⏰ Hẹn giờ",
            variable=self.chk_auto_var,
            command=self.toggle_schedule
        )
        self.chk_auto.pack(side="left", padx=4)

        tpl_row = ttk.Frame(frame_action)
        tpl_row.pack(fill="x", pady=3)
        ttk.Label(tpl_row, text="Mẫu bài đăng:").pack(side="left")
        self.cmb_template = ttk.Combobox(
            tpl_row,
            values=[TEMPLATE_EXPAT_EN, TEMPLATE_VIETNAMESE],
            state="readonly",
            width=32
        )
        self.cmb_template.set(TEMPLATE_EXPAT_EN)
        self.cmb_template.pack(side="left", padx=6)
        self.cmb_template.bind("<<ComboboxSelected>>", lambda e: self.on_room_select(None))

        ttk.Button(tpl_row, text="🎲 Tạo lại biến thể nội dung", command=lambda: self.on_room_select(None, spin=True)).pack(side="left", padx=4)

        self.lbl_auto_progress = ttk.Label(
            tpl_row,
            text="🎯 Chế độ tự động: Sẵn sàng (Duyệt đủ 10 link bài báo cáo)",
            font=("Segoe UI", 9, "bold"),
            foreground="#0369a1"
        )
        self.lbl_auto_progress.pack(side="right", padx=6)

        preview_box = ttk.Frame(frame_action)
        preview_box.pack(fill="x", pady=3)
        ttk.Label(preview_box, text="Xem trước nội dung\n(Có thể sửa tay):").grid(row=0, column=0, sticky="nw")
        self.txt_message = scrolledtext.ScrolledText(preview_box, height=5, font=("Segoe UI", 9))
        self.txt_message.grid(row=0, column=1, sticky="ew", padx=6)
        preview_box.columnconfigure(1, weight=1)

        frame_rooms = ttk.LabelFrame(self.root, text="📋 Danh sách phòng trống sẵn sàng đăng (Bấm vào căn để chọn)", padding=8)
        frame_rooms.pack(fill="x", padx=12, pady=4)

        # Thanh lọc tòa nhà và ẩn/hiện căn
        room_filter_bar = ttk.Frame(frame_rooms)
        room_filter_bar.pack(fill="x", pady=(0, 4))

        ttk.Label(room_filter_bar, text="🏢 Lọc theo tòa:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 4))
        self.cmb_filter_building = ttk.Combobox(room_filter_bar, state="readonly", width=30)
        self.cmb_filter_building.set("Tất cả tòa nhà")
        self.cmb_filter_building.pack(side="left", padx=(0, 8))
        self.cmb_filter_building.bind("<<ComboboxSelected>>", lambda e: self.render_rooms_tree())

        self.chk_show_hidden = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            room_filter_bar,
            text="👁️ Hiện cả căn đã ẩn (để xem / bỏ ẩn)",
            variable=self.chk_show_hidden,
            command=self.render_rooms_tree
        ).pack(side="left", padx=(0, 8))

        self.lbl_room_count_stat = ttk.Label(
            room_filter_bar,
            text="📊 Hiển thị: 0 / 0 căn",
            font=("Segoe UI", 9, "bold"),
            foreground="#0284c7"
        )
        self.lbl_room_count_stat.pack(side="right")

        cols = ("unit", "building", "area", "type", "price_usd", "price", "photos")
        self.tree = ttk.Treeview(frame_rooms, columns=cols, show="headings", height=5)
        self.tree.heading("unit", text="Căn")
        self.tree.heading("building", text="Tòa nhà / Địa chỉ")
        self.tree.heading("area", text="Diện tích")
        self.tree.heading("type", text="Loại phòng / Tiện ích")
        self.tree.heading("price_usd", text="Giá USD")
        self.tree.heading("price", text="Giá VND")
        self.tree.heading("photos", text="Kho ảnh")

        self.tree.column("unit", width=85, anchor="center")
        self.tree.column("building", width=180)
        self.tree.column("area", width=70, anchor="center")
        self.tree.column("type", width=250)
        self.tree.column("price_usd", width=75, anchor="e")
        self.tree.column("price", width=105, anchor="e")
        self.tree.column("photos", width=85, anchor="center")
        self.tree.pack(fill="x")
        self.tree.bind("<<TreeviewSelect>>", self.on_room_select)
        self.setup_tree_context_menu()

        # Thanh công cụ kho ảnh & điều khiển ẩn/hiện cho từng căn
        room_photo_bar = ttk.Frame(frame_rooms)
        room_photo_bar.pack(fill="x", pady=(5, 1))

        self.lbl_room_photo_info = ttk.Label(
            room_photo_bar,
            text="📁 Kho ảnh căn đang chọn: (Chưa chọn căn)",
            font=("Segoe UI", 9),
            foreground="#0284c7"
        )
        self.lbl_room_photo_info.pack(side="left", fill="x", expand=True)

        self.btn_hide_room = ttk.Button(
            room_photo_bar,
            text="👁️ Ẩn căn này",
            command=self.hide_selected_room
        )
        self.btn_hide_room.pack(side="right", padx=(2, 0))

        self.btn_hide_building = ttk.Button(
            room_photo_bar,
            text="🏢 Ẩn cả tòa",
            command=self.hide_selected_building
        )
        self.btn_hide_building.pack(side="right", padx=(2, 0))

        self.btn_unhide_room = ttk.Button(
            room_photo_bar,
            text="🔓 Bỏ ẩn",
            command=self.unhide_selected_room
        )
        self.btn_unhide_room.pack(side="right", padx=(2, 0))

        self.btn_reset_hidden = ttk.Button(
            room_photo_bar,
            text="🔄 Bỏ ẩn tất cả",
            command=self.reset_all_hidden
        )
        self.btn_reset_hidden.pack(side="right", padx=(2, 0))

        self.btn_set_room_photo = ttk.Button(
            room_photo_bar,
            text="📁 Chọn kho ảnh",
            command=self.trigger_choose_room_photo_dir
        )
        self.btn_set_room_photo.pack(side="right", padx=(4, 0))

        self.btn_open_room_photo = ttk.Button(
            room_photo_bar,
            text="📂 Mở thư mục",
            command=self.trigger_open_room_photo_dir
        )
        self.btn_open_room_photo.pack(side="right", padx=(2, 0))

        frame_log = ttk.LabelFrame(self.root, text="📝 Nhật ký hoạt động Đồng bộ, Kiểm tra bị kích & Đăng bài", padding=8)
        frame_log.pack(fill="both", expand=True, padx=12, pady=4)

        self.log_box = scrolledtext.ScrolledText(frame_log, height=7, state="disabled", font=("Consolas", 9), bg="#181b20", fg="#38bdf8")
        self.log_box.pack(fill="both", expand=True)

        self.status_bar = ttk.Label(self.root, text="🟢 Hệ thống FB Groups Poster V6 sẵn sàng.", relief="sunken", anchor="w", padding=3)
        self.status_bar.pack(fill="x", side="bottom")

    # ----------------- MỞ CHROME GỐC ĐĂNG NHẬP FACEBOOK & GOOGLE (KHÔNG BỊ CHẶN BẢO MẬT) -----------------
    def trigger_open_login_browser(self):
        if self.is_posting:
            messagebox.showwarning("Đang xử lý", "Hệ thống đang chạy một tác vụ. Vui lòng chờ tác vụ hoàn tất.")
            return

        def worker():
            self.is_posting = True
            try:
                chrome_path = find_chrome_executable()
                report_url = self.ent_report_sheet.get().strip() or DEFAULT_REPORT_SHEET_URL
                self.log("🌐 Đang mở Google Chrome nguyên bản (không dính cờ tự động hóa để tránh bị Google chặn)...")
                cmd = [
                    chrome_path,
                    f"--user-data-dir={FB_CHROME_PROFILE_DIR}",
                    "https://www.facebook.com",
                    report_url
                ]
                proc = subprocess.Popen(cmd)
                self.log("👉 Đã mở Google Chrome! Bạn hãy thong thả đăng nhập Facebook và Google trên 2 tab đang mở.")
                self.log("💡 Sau khi đăng nhập thành công cả 2 bên, bạn chỉ cần ĐÓNG CỬA SỔ CHROME lại.")
                proc.wait()
                self.log("✅ Đã ghi nhận đóng trình duyệt Chrome! Toàn bộ phiên đăng nhập đã được lưu vĩnh viễn.")
            except Exception as e:
                self.log(f"❌ Lỗi mở Chrome đăng nhập: {e}")
            finally:
                self.is_posting = False

        threading.Thread(target=worker, daemon=True).start()

    # ----------------- TRÍCH XUẤT & ĐỒNG BỘ CÁC NHÓM ĐÃ ĐĂNG TỪ SHEET BÁO CÁO -----------------
    def trigger_pull_groups_from_report_sheet(self):
        report_url = self.ent_report_sheet.get().strip()
        if not report_url or "docs.google.com/spreadsheets" not in report_url:
            messagebox.showwarning("Thiếu link", "Vui lòng kiểm tra lại link Google Sheet Báo Cáo.")
            return

        def worker():
            self.is_posting = True
            self.set_action_buttons_state("disabled")
            try:
                self.log("📥 Đang đọc dữ liệu từ Sheet Báo Cáo để trích xuất danh sách nhóm đăng được...")
                m_id = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", report_url)
                m_gid = re.search(r"[#&?]gid=([0-9]+)", report_url)
                if not m_id:
                    self.log("❌ Không nhận diện được ID của Sheet Báo Cáo.")
                    return

                s_id = m_id.group(1)
                g_id = m_gid.group(1) if m_gid else "0"
                csv_url = f"https://docs.google.com/spreadsheets/d/{s_id}/export?format=csv&gid={g_id}"

                content = ""
                try:
                    req = Request(csv_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urlopen(req, timeout=15) as resp:
                        content = resp.read().decode("utf-8-sig")
                except Exception as e_url:
                    self.log(f"🔒 Sheet Báo Cáo yêu cầu đăng nhập Google ({e_url}) -> Đang đọc qua Chrome Profile...")
                    with sync_playwright() as p:
                        ctx = p.chromium.launch_persistent_context(
                            user_data_dir=FB_CHROME_PROFILE_DIR,
                            channel="chrome",
                            headless=False,
                            viewport={"width": 1200, "height": 800},
                            ignore_default_args=["--enable-automation"],
                            args=["--disable-blink-features=AutomationControlled", "--disable-notifications"]
                        )
                        ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
                        pg = ctx.pages[0] if ctx.pages else ctx.new_page()
                        pg.goto(report_url, wait_until="domcontentloaded", timeout=45000)
                        time.sleep(3.0)

                        if "accounts.google.com" in pg.url:
                            self.log("🔐 Vui lòng đăng nhập Google trên cửa sổ Chrome vừa mở (chờ bạn đăng nhập tối đa 180s)...")
                            logged_in = False
                            for _ in range(180):
                                if "accounts.google.com" not in pg.url and "docs.google.com/spreadsheets/d/" in pg.url:
                                    logged_in = True
                                    self.log("✅ Đã nhận diện đăng nhập Google thành công! Đang tải dữ liệu...")
                                    time.sleep(3.0)
                                    break
                                time.sleep(1.0)
                            if not logged_in:
                                self.log("⚠️ Hết thời gian chờ đăng nhập Google (180s). Vui lòng thử lại sau khi đăng nhập xong.")
                                ctx.close()
                                return

                        try:
                            content = pg.evaluate("""async (url) => {
                                const resp = await fetch(url);
                                if (!resp.ok) throw new Error("HTTP " + resp.status);
                                return await resp.text();
                            }""", csv_url)
                        except Exception as e_fetch:
                            self.log(f"⚠️ Chuyển sang tải trực tiếp bảng tính: {e_fetch}")
                            try:
                                pg.goto(csv_url, wait_until="domcontentloaded", timeout=20000)
                                time.sleep(2.0)
                                content = pg.locator("body").inner_text()
                            except Exception:
                                pass
                        ctx.close()

                if not content:
                    self.log("❌ Không lấy được nội dung Sheet Báo Cáo (chưa đăng nhập Google hoặc không có quyền truy cập).")
                    return

                rows = list(csv.reader(io.StringIO(content)))
                groups_info_map = {}
                share_links_to_resolve = []

                for r_idx, row in enumerate(rows, start=1):
                    if r_idx < 5 or len(row) < 6:
                        continue
                    g_name = row[1].strip()
                    link_val = row[3].strip()
                    status_raw = row[5].strip()
                    status_val = status_raw.lower()

                    if not link_val or "facebook.com" not in link_val:
                        continue
                    if "chưa đăng" in status_val or "giới hạn" in status_val or "lỗi" in status_val:
                        continue

                    is_instant_confirmed = any(k in status_val for k in ["đăng ngay", "instant", "không duyệt", "auto approve"])
                    grp_type = "INSTANT" if is_instant_confirmed else "PENDING"

                    m_grp = re.search(r"(https?://(?:www\.|m\.)?facebook\.com/groups/[^/?#]+)", link_val)
                    if m_grp:
                        base_u = normalize_group_base_url(m_grp.group(1))
                        # Các dòng trên cùng (dòng 5, 6...) là bài đăng gần đây nhất, ưu tiên trạng thái mới nhất
                        if base_u not in groups_info_map:
                            groups_info_map[base_u] = {
                                "name": g_name or base_u,
                                "type": grp_type,
                                "last_status": "Đã đăng" if grp_type == "INSTANT" else "Đang chờ phê duyệt",
                                "note": "Tự động đăng ngay không kiểm duyệt" if grp_type == "INSTANT" else "Quản lý bài viết - Chờ quản trị viên phê duyệt"
                            }
                    elif "/share/p/" in link_val or "set=g." in link_val:
                        if g_name and g_name not in [x[0] for x in share_links_to_resolve]:
                            share_links_to_resolve.append((g_name, link_val, grp_type, "Đã đăng" if grp_type == "INSTANT" else "Đang chờ phê duyệt"))

                added_count = 0
                for b_u, info in groups_info_map.items():
                    if self.add_or_update_group(b_u, info["name"], group_type=info["type"], last_status=info["last_status"], note=info.get("note", ""), silent=True):
                        added_count += 1

                if share_links_to_resolve:
                    self.log(f"🔎 Tìm thấy {len(share_links_to_resolve)} nhóm dùng link rút gọn (/share/p/...), đang mở trình duyệt phân giải link nhóm gốc...")
                    with sync_playwright() as p:
                        context = p.chromium.launch_persistent_context(
                            user_data_dir=FB_CHROME_PROFILE_DIR,
                            channel="chrome",
                            headless=False,
                            viewport={"width": 1200, "height": 800},
                            ignore_default_args=["--enable-automation"],
                            args=["--disable-blink-features=AutomationControlled", "--disable-notifications"]
                        )
                        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
                        page = context.pages[0] if context.pages else context.new_page()
                        for g_n, s_url, s_type, s_status in share_links_to_resolve[:12]:
                            try:
                                m_set = re.search(r"set=g\.(\d+)", s_url)
                                if m_set:
                                    b_u = f"https://www.facebook.com/groups/{m_set.group(1)}/"
                                    if self.add_or_update_group(b_u, g_n, group_type=s_type, last_status=s_status, silent=True):
                                        added_count += 1
                                    continue

                                page.goto(s_url, wait_until="domcontentloaded", timeout=25000)
                                time.sleep(3.0)
                                m_resolved = re.search(r"(https?://(?:www\.|m\.)?facebook\.com/groups/[^/?#]+)", page.url)
                                if m_resolved:
                                    b_u = normalize_group_base_url(m_resolved.group(1))
                                    if self.add_or_update_group(b_u, g_n, group_type=s_type, last_status=s_status, silent=True):
                                        added_count += 1
                            except Exception:
                                continue
                        context.close()

                self.root.after(0, self.refresh_clean_groups_display)
                instant_count = sum(1 for g in self.clean_groups if g.get("type", "INSTANT") == "INSTANT")
                pending_count = sum(1 for g in self.clean_groups if g.get("type") == "PENDING")
                self.log(f"✅ Đã đồng bộ xong từ Sheet Báo Cáo! Tổng: {len(self.clean_groups)} nhóm ({instant_count} 🟢 Đăng ngay | {pending_count} 🟡 Chờ duyệt).")
                if instant_count > 0:
                    self.root.after(0, self.copy_instant_groups_to_active)
            except Exception as e:
                self.log(f"❌ Lỗi đọc Sheet Báo Cáo: {e}")
            finally:
                self.is_posting = False
                self.set_action_buttons_state("normal")

        threading.Thread(target=worker, daemon=True).start()

    # ----------------- QUẢN LÝ KHO NHÓM ĐÃ PHÂN LOẠI (🟢 ĐĂNG NGAY / 🟡 CHỜ DUYỆT) -----------------
    def refresh_clean_groups_display(self):
        self.txt_clean_groups.config(state="normal")
        self.txt_clean_groups.delete("1.0", "end")

        self.txt_clean_groups.tag_config("tag_instant", foreground="#16a34a", font=("Segoe UI", 9, "bold"))
        self.txt_clean_groups.tag_config("tag_pending", foreground="#d97706", font=("Segoe UI", 9, "bold"))
        self.txt_clean_groups.tag_config("tag_link", foreground="#0f172a", font=("Segoe UI", 9))
        self.txt_clean_groups.tag_config("tag_name", foreground="#64748b", font=("Segoe UI", 8, "italic"))

        instant_count = 0
        pending_count = 0

        # Sắp xếp nhóm: Đăng ngay (INSTANT) lên trước, Chờ duyệt (PENDING) xuống sau
        sorted_groups = sorted(self.clean_groups, key=lambda x: (x.get("type") == "PENDING", x.get("name", "")))

        for item in sorted_groups:
            grp_type = item.get("type", "INSTANT")
            if grp_type == "PENDING":
                pending_count += 1
                prefix = "[🟡 CHỜ DUYỆT] "
                tag_prefix = "tag_pending"
            else:
                instant_count += 1
                prefix = "[🟢 ĐĂNG NGAY] "
                tag_prefix = "tag_instant"

            self.txt_clean_groups.insert("end", prefix, tag_prefix)
            self.txt_clean_groups.insert("end", f"{item['url']} ", "tag_link")
            if item.get("name"):
                self.txt_clean_groups.insert("end", f"# {item['name']}", "tag_name")
            self.txt_clean_groups.insert("end", "\n")

        self.lbl_clean_count.config(
            text=f"Đã lưu: {len(self.clean_groups)} nhóm ({instant_count} 🟢 Đăng ngay | {pending_count} 🟡 Chờ duyệt)"
        )

    def add_or_update_group(
        self,
        group_url,
        group_name="",
        group_type="INSTANT",
        last_status="Đã đăng",
        member_status="Đã là thành viên",
        note="",
        silent=False
    ):
        base_url = normalize_group_base_url(group_url)
        for g in self.clean_groups:
            if normalize_group_base_url(g["url"]) == base_url:
                changed = (
                    g.get("type") != group_type or
                    g.get("last_status") != last_status or
                    (member_status and g.get("member_status") != member_status)
                )
                g["type"] = group_type
                g["last_status"] = last_status
                if member_status:
                    g["member_status"] = member_status
                if note:
                    g["note"] = note
                elif "note" not in g:
                    g["note"] = "Đăng ngay không kiểm duyệt" if group_type == "INSTANT" else "Admin kiểm duyệt bài trước khi hiện"
                if group_name and (not g.get("name") or g.get("name") == base_url):
                    g["name"] = group_name
                g["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                if changed:
                    self.save_json_list(CLEAN_GROUPS_FILE, self.clean_groups)
                    if not silent:
                        self.root.after(0, self.refresh_clean_groups_display)
                return False

        # Thêm mới
        default_note = note or ("Đăng ngay không kiểm duyệt" if group_type == "INSTANT" else "Admin kiểm duyệt bài trước khi hiện")
        self.clean_groups.append({
            "url": base_url,
            "name": group_name or base_url,
            "type": group_type,
            "member_status": member_status or "Đã là thành viên",
            "last_status": last_status,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "note": default_note
        })
        self.save_json_list(CLEAN_GROUPS_FILE, self.clean_groups)
        if not silent:
            self.root.after(0, self.refresh_clean_groups_display)
            tag_name = "🟢 ĐĂNG NGAY" if group_type == "INSTANT" else "🟡 CHỜ DUYỆT"
            self.log(f"⭐ Đã lưu '{group_name or base_url}' vào Kho Nhóm ({tag_name})!")
        return True

    def add_to_clean_groups(self, group_url, group_name="", silent=False):
        return self.add_or_update_group(group_url, group_name, group_type="INSTANT", last_status="Đã đăng", silent=silent)

    def remove_from_clean_groups(self, group_url):
        base_url = normalize_group_base_url(group_url)
        before = len(self.clean_groups)
        self.clean_groups = [g for g in self.clean_groups if normalize_group_base_url(g["url"]) != base_url]
        if len(self.clean_groups) < before:
            self.save_json_list(CLEAN_GROUPS_FILE, self.clean_groups)
            self.root.after(0, self.refresh_clean_groups_display)

    def copy_instant_groups_to_active(self):
        urls = [g["url"] for g in self.clean_groups if g.get("type", "INSTANT") == "INSTANT"]
        if not urls:
            messagebox.showinfo("Chưa có nhóm", "Chưa có nhóm nào được phân loại '🟢 Đăng ngay'.")
            return
        self.txt_groups.delete("1.0", "end")
        self.txt_groups.insert("1.0", "\n".join(urls))
        self.log(f"🟢 Đã nạp {len(urls)} nhóm ĐĂNG NGAY (Không kiểm duyệt) sang ô đăng bài!")

    def copy_all_groups_to_active(self):
        urls = [g["url"] for g in self.clean_groups if g.get("url")]
        if not urls:
            messagebox.showinfo("Chưa có nhóm", "Kho nhóm hiện chưa có link nào.")
            return
        self.txt_groups.delete("1.0", "end")
        self.txt_groups.insert("1.0", "\n".join(urls))
        self.log(f"📋 Đã nạp toàn bộ {len(urls)} nhóm (cả Đăng ngay & Chờ duyệt) sang ô đăng bài!")

    def copy_clean_groups_to_active(self):
        self.copy_instant_groups_to_active()

    def set_action_buttons_state(self, state):
        btns = [
            getattr(self, "btn_post_selected", None),
            getattr(self, "btn_auto_post_10", None),
            getattr(self, "btn_load_sheet", None),
            getattr(self, "btn_auto_join", None),
            getattr(self, "btn_pull_from_report", None),
            getattr(self, "btn_sync_groups_drive", None),
            getattr(self, "btn_pull_groups_drive", None),
        ]
        for btn in btns:
            if btn is not None:
                try:
                    btn.config(state=state)
                except Exception:
                    pass

    # ----------------- ĐỒNG BỘ KHO NHÓM LÊN TAB DANH_SACH_NHOM (GOOGLE DRIVE) -----------------
    def sync_groups_to_google_sheet(self, context=None, silent=False):
        if not self.clean_groups:
            if not silent:
                self.log("⚠️ Kho Nhóm đang trống, không có nhóm nào để đồng bộ lên Google Sheet.")
            return False

        report_url = self.ent_report_sheet.get().strip() or DEFAULT_REPORT_SHEET_URL
        if not report_url or "docs.google.com/spreadsheets" not in report_url:
            if not silent:
                self.log("⚠️ Link Google Sheet Báo Cáo không hợp lệ.")
            return False

        close_context_after = False
        p_instance = None
        if context is None:
            close_context_after = True
            p_instance = sync_playwright().start()
            context = p_instance.chromium.launch_persistent_context(
                user_data_dir=FB_CHROME_PROFILE_DIR,
                channel="chrome",
                headless=False,
                viewport={"width": 1280, "height": 850},
                ignore_default_args=["--enable-automation"],
                args=["--disable-blink-features=AutomationControlled", "--disable-notifications"]
            )
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        sheet_page = context.new_page()
        try:
            self.log(f"☁️ Đang mở Google Sheet để đồng bộ {len(self.clean_groups)} nhóm vào Tab 'Danh_Sach_Nhom'...")
            sheet_page.goto(report_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(4.0)

            if "accounts.google.com" in sheet_page.url:
                self.log("🔐 Chrome Profile chưa đăng nhập Google! Mời bạn đăng nhập trên tab vừa mở (chờ tối đa 180s)...")
                logged_in = False
                for _ in range(180):
                    if "accounts.google.com" not in sheet_page.url and "docs.google.com/spreadsheets/d/" in sheet_page.url:
                        logged_in = True
                        self.log("✅ Đã nhận diện đăng nhập Google thành công! Tiếp tục đồng bộ...")
                        time.sleep(3.0)
                        break
                    time.sleep(1.0)
                if not logged_in:
                    self.log("⚠️ Hết thời gian chờ đăng nhập Google (180s). Bỏ qua đồng bộ nhóm lên Sheet.")
                    return False

            # Tìm tab Danh_Sach_Nhom trên thanh tab
            tab_info = sheet_page.evaluate("""() => {
                const tabs = Array.from(document.querySelectorAll('.docs-sheet-tab'));
                for (const t of tabs) {
                    const txt = (t.innerText || '').trim();
                    if (txt.includes('Danh_Sach_Nhom') || txt.includes('Danh Sách Nhóm') || txt.includes('Kho_Nhom')) {
                        const r = t.getBoundingClientRect();
                        return { found: true, text: txt, x: r.x + r.width/2, y: r.y + r.height/2 };
                    }
                }
                return { found: false };
            }""")

            if tab_info.get("found"):
                sheet_page.mouse.click(tab_info["x"], tab_info["y"])
                time.sleep(2.5)
            else:
                self.log("📑 Chưa có tab 'Danh_Sach_Nhom', đang tạo tab mới trên Google Sheet...")
                add_btn_rect = sheet_page.evaluate("""() => {
                    const btn = document.querySelector('.docs-sheet-add-button, #add-sheet-button, div[aria-label*=\"Thêm trang tính\"], div[aria-label*=\"Add Sheet\"]');
                    if (btn) {
                        const r = btn.getBoundingClientRect();
                        return { found: true, x: r.x + r.width/2, y: r.y + r.height/2 };
                    }
                    return { found: false };
                }""")
                if add_btn_rect.get("found"):
                    sheet_page.mouse.click(add_btn_rect["x"], add_btn_rect["y"])
                else:
                    sheet_page.keyboard.press("Shift+F11")
                time.sleep(3.5)

                active_rect = sheet_page.evaluate("""() => {
                    const t = document.querySelector('.docs-sheet-active-tab');
                    if (t) {
                        const r = t.getBoundingClientRect();
                        return { found: true, x: r.x + r.width/2, y: r.y + r.height/2 };
                    }
                    return { found: false };
                }""")
                if active_rect.get("found"):
                    sheet_page.mouse.dblclick(active_rect["x"], active_rect["y"])
                    time.sleep(0.5)
                    sheet_page.keyboard.press("Control+A")
                    sheet_page.keyboard.type("Danh_Sach_Nhom")
                    sheet_page.keyboard.press("Enter")
                    time.sleep(2.0)

            # KIỂM TRA BẢO MẬT TUYỆT ĐỐI: CHỈ THAO TÁC KHI TAB ĐANG CHỌN LÀ DANH_SACH_NHOM
            active_tab_name = sheet_page.evaluate("""() => {
                const t = document.querySelector('.docs-sheet-active-tab');
                return t ? t.innerText.trim() : '';
            }""")

            if "Trang tính1" in active_tab_name or "Danh_Sach_Nhom" not in active_tab_name:
                self.log(f"🛡️ CẢNH BÁO BẢO VỆ: Thẻ hiện tại là '{active_tab_name}' (không phải Danh_Sach_Nhom). HỦY THAO TÁC XÓA ĐỂ BẢO VỆ DỮ LIỆU CŨ!")
                return False

            self.log(f"📑 Đã xác nhận an toàn trên tab '{active_tab_name}', tiến hành cập nhật bảng 30 nhóm...")

            # Chọn ô A1
            name_box = sheet_page.locator("#t-name-box").first
            if name_box.count() > 0:
                name_box.click()
                time.sleep(0.3)
                sheet_page.keyboard.press("Control+A")
                sheet_page.keyboard.type("A1")
                sheet_page.keyboard.press("Enter")
                time.sleep(0.5)

            # Xoá nội dung cũ trên sheet để tránh sót dòng thừa
            sheet_page.keyboard.press("Control+A")
            time.sleep(0.2)
            sheet_page.keyboard.press("Delete")
            time.sleep(0.4)

            # Định vị lại A1
            if name_box.count() > 0:
                name_box.click()
                time.sleep(0.2)
                sheet_page.keyboard.press("Control+A")
                sheet_page.keyboard.type("A1")
                sheet_page.keyboard.press("Enter")
                time.sleep(0.5)

            # Tạo bảng TSV
            headers = ["STT", "Tên Nhóm", "Link Nhóm (Facebook)", "Phân Loại", "Trạng Thái Thành Viên", "Trạng Thái Đăng Cuối", "Ngày Cập Nhật", "Ghi Chú"]
            tsv_lines = ["\t".join(headers)]

            sorted_groups = sorted(self.clean_groups, key=lambda x: (x.get("type") == "PENDING", x.get("name", "")))
            instant_n = 0
            pending_n = 0
            for i, g in enumerate(sorted_groups, start=1):
                g_name = str(g.get("name") or g.get("url") or "").replace("\t", " ").replace("\n", " ").strip()
                g_url = str(g.get("url") or "").replace("\t", " ").replace("\n", " ").strip()
                g_type = g.get("type", "INSTANT")
                if g_type == "PENDING":
                    pending_n += 1
                    cat_label = "🟡 CHỜ DUYỆT"
                else:
                    instant_n += 1
                    cat_label = "🟢 ĐĂNG NGAY"

                mem_stat = str(g.get("member_status") or "Đã là thành viên").replace("\t", " ").replace("\n", " ").strip()
                last_stat = str(g.get("last_status") or ("Đã đăng" if g_type == "INSTANT" else "Chờ phê duyệt")).replace("\t", " ").replace("\n", " ").strip()
                updated_at = str(g.get("updated_at") or g.get("verified_at") or datetime.now().strftime("%Y-%m-%d %H:%M")).replace("\t", " ").replace("\n", " ").strip()
                note = str(g.get("note") or ("Tự động đăng ngay, không duyệt bài" if g_type == "INSTANT" else "Bài đăng phải chờ Admin duyệt")).replace("\t", " ").replace("\n", " ").strip()

                tsv_lines.append(f"{i}\t{g_name}\t{g_url}\t{cat_label}\t{mem_stat}\t{last_stat}\t{updated_at}\t{note}")

            tsv_text = "\n".join(tsv_lines)
            pyperclip.copy(tsv_text)
            time.sleep(0.3)
            sheet_page.keyboard.press("Control+V")
            time.sleep(2.5)

            local_master_csv = Path(FB_CACHE_DIR) / "fb_groups_master.csv"
            with open(local_master_csv, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for line in tsv_lines[1:]:
                    writer.writerow(line.split("\t"))

            self.log(f"✅ ĐÃ ĐỒNG BỘ XONG {len(sorted_groups)} NHÓM lên Tab 'Danh_Sach_Nhom' trên Google Drive! ({instant_n} 🟢 Đăng ngay | {pending_n} 🟡 Chờ duyệt)")
            return True
        except Exception as e:
            self.log(f"❌ Lỗi đồng bộ Kho Nhóm lên Google Sheet: {e}")
            return False
        finally:
            try:
                sheet_page.close()
            except Exception:
                pass
            if close_context_after and context:
                try:
                    context.close()
                except Exception:
                    pass
            if p_instance:
                try:
                    p_instance.stop()
                except Exception:
                    pass

    # ----------------- TẢI KHO NHÓM TỪ TAB DANH_SACH_NHOM (GOOGLE DRIVE) -----------------
    def pull_groups_from_groups_sheet(self, context=None):
        report_url = self.ent_report_sheet.get().strip() or DEFAULT_REPORT_SHEET_URL
        if not report_url or "docs.google.com/spreadsheets" not in report_url:
            self.log("⚠️ Link Google Sheet Báo Cáo không hợp lệ.")
            return False

        m_id = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", report_url)
        if not m_id:
            self.log("❌ Không nhận diện được ID của Sheet.")
            return False
        s_id = m_id.group(1)

        close_context_after = False
        p_instance = None
        if context is None:
            close_context_after = True
            p_instance = sync_playwright().start()
            context = p_instance.chromium.launch_persistent_context(
                user_data_dir=FB_CHROME_PROFILE_DIR,
                channel="chrome",
                headless=False,
                viewport={"width": 1280, "height": 850},
                ignore_default_args=["--enable-automation"],
                args=["--disable-blink-features=AutomationControlled", "--disable-notifications"]
            )
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        sheet_page = context.new_page()
        try:
            self.log("📥 Đang kết nối tới Google Sheet để đọc Tab 'Danh_Sach_Nhom'...")
            sheet_page.goto(report_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(4.0)

            if "accounts.google.com" in sheet_page.url:
                self.log("🔐 Chrome Profile chưa đăng nhập Google! Mời bạn đăng nhập trên tab vừa mở (chờ tối đa 180s)...")
                logged_in = False
                for _ in range(180):
                    if "accounts.google.com" not in sheet_page.url and "docs.google.com/spreadsheets/d/" in sheet_page.url:
                        logged_in = True
                        self.log("✅ Đã nhận diện đăng nhập Google thành công! Tiếp tục đọc dữ liệu...")
                        time.sleep(3.0)
                        break
                    time.sleep(1.0)
                if not logged_in:
                    self.log("⚠️ Hết thời gian chờ đăng nhập Google (180s). Bỏ qua.")
                    return False

            tab_info = sheet_page.evaluate("""() => {
                const tabs = Array.from(document.querySelectorAll('.docs-sheet-tab'));
                for (const t of tabs) {
                    const txt = (t.innerText || '').trim();
                    if (txt.includes('Danh_Sach_Nhom') || txt.includes('Danh Sách Nhóm') || txt.includes('Kho_Nhom')) {
                        const r = t.getBoundingClientRect();
                        return { found: true, name: txt, x: r.x + r.width/2, y: r.y + r.height/2 };
                    }
                }
                return { found: false };
            }""")

            if not tab_info.get("found"):
                self.log("ℹ️ Chưa tìm thấy Tab 'Danh_Sach_Nhom' trên Sheet này. Hãy bấm '☁️ Lưu Kho Nhóm lên Drive' để tạo Tab trước.")
                return False

            sheet_page.mouse.click(tab_info["x"], tab_info["y"])
            time.sleep(2.5)

            m_gid = re.search(r"gid=([0-9]+)", sheet_page.url)
            gid = m_gid.group(1) if m_gid else None

            if not gid or gid == "0":
                self.log("⚠️ Không nhận diện được GID riêng của Tab 'Danh_Sach_Nhom'. Hủy tải để tránh nhầm sang Trang tính 1.")
                return False

            csv_url = f"https://docs.google.com/spreadsheets/d/{s_id}/export?format=csv&gid={gid}"
            content = sheet_page.evaluate("""async (url) => {
                const resp = await fetch(url);
                if (!resp.ok) throw new Error("HTTP " + resp.status);
                return await resp.text();
            }""", csv_url)

            if not content:
                self.log("❌ Không lấy được nội dung Tab 'Danh_Sach_Nhom'.")
                return False

            rows = list(csv.reader(io.StringIO(content)))
            if len(rows) < 2:
                self.log("⚠️ Tab 'Danh_Sach_Nhom' hiện chưa có dữ liệu nhóm nào.")
                return False

            loaded_count = 0
            for r_idx, row in enumerate(rows[1:], start=1):
                if len(row) < 3:
                    continue
                g_name = row[1].strip()
                g_url = row[2].strip()
                cat_val = row[3].strip() if len(row) > 3 else ""
                mem_stat = row[4].strip() if len(row) > 4 else "Đã là thành viên"
                last_stat = row[5].strip() if len(row) > 5 else ""
                updated_at = row[6].strip() if len(row) > 6 else ""
                note = row[7].strip() if len(row) > 7 else ""

                if not g_url or "facebook.com" not in g_url:
                    continue

                is_pending = any(k in cat_val.upper() for k in ["CHỜ", "PENDING", "DUYỆT"])
                grp_type = "PENDING" if is_pending else "INSTANT"

                self.add_or_update_group(
                    g_url,
                    group_name=g_name,
                    group_type=grp_type,
                    last_status=last_stat or ("Đã đăng" if grp_type == "INSTANT" else "Chờ duyệt"),
                    member_status=mem_stat,
                    note=note,
                    silent=True
                )
                loaded_count += 1

            self.save_json_list(CLEAN_GROUPS_FILE, self.clean_groups)
            self.root.after(0, self.refresh_clean_groups_display)

            instant_count = sum(1 for g in self.clean_groups if g.get("type", "INSTANT") == "INSTANT")
            pending_count = sum(1 for g in self.clean_groups if g.get("type") == "PENDING")
            self.log(f"✅ ĐÃ TẢI XONG {loaded_count} NHÓM TỪ GOOGLE DRIVE! Tổng hiện tại: {len(self.clean_groups)} nhóm ({instant_count} 🟢 Đăng ngay | {pending_count} 🟡 Chờ duyệt).")
            return True
        except Exception as e:
            self.log(f"❌ Lỗi tải nhóm từ Google Sheet: {e}")
            return False
        finally:
            try:
                sheet_page.close()
            except Exception:
                pass
            if close_context_after and context:
                try:
                    context.close()
                except Exception:
                    pass
            if p_instance:
                try:
                    p_instance.stop()
                except Exception:
                    pass

    def trigger_sync_groups_to_drive(self):
        if self.is_posting:
            messagebox.showwarning("Đang bận", "Hệ thống đang thực hiện tác vụ trình duyệt. Vui lòng chờ hoàn tất.")
            return

        def worker():
            self.is_posting = True
            self.set_action_buttons_state("disabled")
            try:
                self.sync_groups_to_google_sheet()
            finally:
                self.is_posting = False
                self.set_action_buttons_state("normal")

        threading.Thread(target=worker, daemon=True).start()

    def trigger_pull_groups_from_drive(self):
        if self.is_posting:
            messagebox.showwarning("Đang bận", "Hệ thống đang thực hiện tác vụ trình duyệt. Vui lòng chờ hoàn tất.")
            return

        def worker():
            self.is_posting = True
            self.set_action_buttons_state("disabled")
            try:
                self.pull_groups_from_groups_sheet()
            finally:
                self.is_posting = False
                self.set_action_buttons_state("normal")

        threading.Thread(target=worker, daemon=True).start()

    # ----------------- HỆ THỐNG GHI NHẬT KÝ THREAD-SAFE -----------------
    def log(self, text):
        t = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{t}] {text}")

    def process_log_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait()
            self.log_box.config(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.config(state="disabled")
            self.status_bar.config(text=msg)
        self.root.after(100, self.process_log_queue)

    # ----------------- TÌM NHÓM TƯƠNG TỰ DỰ PHÒNG KHI BỊ KÍCH -----------------
    def find_similar_replacement_group(self, page, excluded_urls):
        raw_kw = self.ent_keywords.get().strip()
        keywords = [k.strip() for k in raw_kw.split(",") if k.strip()] or ["Hanoi Massive", "Hanoi Expats"]
        kw = random.choice(keywords)
        try:
            search_url = f"https://www.facebook.com/search/groups/?q={kw.replace(' ', '%20')}"
            self.log(f"🔄 Đang tìm nhóm tương tự theo từ khóa '{kw}' để thay thế nhóm vừa bị kích...")
            page.goto(search_url, wait_until="domcontentloaded", timeout=35000)
            time.sleep(3.5)
            page.mouse.wheel(0, 600)
            time.sleep(1.5)

            for a in page.locator("a[href*='/groups/']").all():
                href = a.get_attribute("href") or ""
                if "/groups/" in href and "/search/" not in href:
                    norm_u = normalize_group_base_url(href)
                    if norm_u not in excluded_urls and norm_u not in self.joined_groups and not norm_u.endswith("/groups/"):
                        page.goto(norm_u, wait_until="domcontentloaded", timeout=35000)
                        time.sleep(3.0)
                        join_btn = page.locator(
                            "div[role='button']:has-text('Tham gia nhóm'), "
                            "div[role='button']:has-text('Join group')"
                        ).first
                        if join_btn.count() > 0 and join_btn.is_visible():
                            join_btn.click()
                            time.sleep(2.5)
                            q_dlg = page.locator("div[role='dialog']:has-text('Trả lời câu hỏi'), div[role='dialog']:has-text('Answer questions')").first
                            if q_dlg.count() > 0:
                                close_b = page.locator("div[role='dialog'] [aria-label='Đóng'], div[role='dialog'] [aria-label='Close']").first
                                if close_b.count() > 0:
                                    close_b.click()
                                continue
                            self.joined_groups.append(norm_u)
                            self.save_json_list(JOINED_GROUPS_FILE, self.joined_groups)
                            self.log(f"🆕 Đã gửi yêu cầu tham gia nhóm thay thế mới: {norm_u}")
                            return norm_u
        except Exception as e:
            self.log(f"⚠️ Không tìm được nhóm thay thế lúc này: {e}")
        return None

    # ----------------- TỰ ĐỘNG TÌM & THAM GIA NHÓM THEO TỪ KHÓA -----------------
    def trigger_search_and_join_groups(self):
        if self.is_posting:
            messagebox.showwarning("Đang bận", "Hệ thống đang thực hiện tác vụ trình duyệt. Vui lòng chờ hoàn tất.")
            return

        raw_kw = self.ent_keywords.get().strip()
        keywords = [k.strip() for k in raw_kw.split(",") if k.strip()]
        if not keywords:
            messagebox.showinfo("Thiếu từ khóa", "Vui lòng nhập ít nhất 1 từ khóa tìm kiếm.")
            return

        try:
            max_join = int(self.spn_max_join.get())
        except Exception:
            max_join = 5

        def worker():
            self.is_posting = True
            self.set_action_buttons_state("disabled")
            joined_this_session = 0
            found_urls_to_append = []

            try:
                self.log(f"🔍 Bắt đầu quét & tham gia nhóm FB với từ khóa: {', '.join(keywords)} (Tối đa {max_join} nhóm)...")
                with sync_playwright() as p:
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=FB_CHROME_PROFILE_DIR,
                        channel="chrome",
                        headless=False,
                        viewport={"width": 1280, "height": 850},
                        ignore_default_args=["--enable-automation"],
                        args=["--disable-blink-features=AutomationControlled", "--disable-notifications"]
                    )
                    context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
                    page = context.pages[0] if context.pages else context.new_page()

                    for kw in keywords:
                        if joined_this_session >= max_join:
                            break
                        search_url = f"https://www.facebook.com/search/groups/?q={kw.replace(' ', '%20')}"
                        self.log(f"🔎 Đang tìm kiếm từ khóa: '{kw}'...")
                        page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
                        time.sleep(random.uniform(3.5, 5.0))

                        if "login" in page.url or page.locator("input[name='email']").count() > 0:
                            self.log("🔐 Chưa đăng nhập Facebook! Mời bạn đăng nhập trên cửa sổ Chrome (chờ tối đa 180s)...")
                            fb_logged_in = False
                            for _ in range(180):
                                if "login" not in page.url and page.locator("input[name='email']").count() == 0:
                                    fb_logged_in = True
                                    self.log("✅ Đã nhận diện đăng nhập Facebook thành công!")
                                    time.sleep(2.0)
                                    break
                                time.sleep(1.0)
                            if not fb_logged_in:
                                self.log("⚠️ Hết thời gian chờ đăng nhập Facebook (180s). Bỏ qua phiên tìm kiếm.")
                                break
                            if "/search/groups/" not in page.url:
                                page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
                                time.sleep(3.0)

                        for _ in range(2):
                            page.mouse.wheel(0, 700)
                            time.sleep(1.5)

                        group_links = page.locator("a[href*='/groups/']").all()
                        candidate_urls = []
                        for a in group_links:
                            try:
                                href = a.get_attribute("href") or ""
                                if "/groups/" in href and "/search/" not in href:
                                    norm_u = normalize_group_base_url(href)
                                    if norm_u not in candidate_urls and not norm_u.endswith("/groups/"):
                                        candidate_urls.append(norm_u)
                            except Exception:
                                continue

                        self.log(f"📌 Tìm thấy {len(candidate_urls)} nhóm tiềm năng cho từ khóa '{kw}'.")

                        for g_url in candidate_urls:
                            if joined_this_session >= max_join:
                                break
                            if g_url in self.joined_groups:
                                continue

                            try:
                                self.log(f"➡️ Truy cập kiểm tra nhóm: {g_url}")
                                page.goto(g_url, wait_until="domcontentloaded", timeout=40000)
                                time.sleep(random.uniform(3.0, 4.5))

                                g_name = g_url
                                h1_loc = page.locator("h1 a, h1 span").first
                                if h1_loc.count() > 0:
                                    t_name = h1_loc.inner_text(timeout=2000).strip()
                                    if t_name and "Facebook" not in t_name:
                                        g_name = t_name

                                join_btn = page.locator(
                                    "div[role='button']:has-text('Tham gia nhóm'), "
                                    "div[role='button']:has-text('Join group'), "
                                    "div[role='button']:has-text('Join Group')"
                                ).first

                                if join_btn.count() > 0 and join_btn.is_visible():
                                    join_btn.click()
                                    time.sleep(3.0)

                                    question_dialog = page.locator("div[role='dialog']:has-text('Trả lời câu hỏi'), div[role='dialog']:has-text('Answer questions')").first
                                    if question_dialog.count() > 0:
                                        self.log(f"⚠️ Nhóm '{g_name}' yêu cầu trả lời câu hỏi kiểm duyệt -> Bỏ qua để tránh treo.")
                                        close_btn = page.locator("div[role='dialog'] [aria-label='Đóng'], div[role='dialog'] [aria-label='Close']").first
                                        if close_btn.count() > 0:
                                            close_btn.click()
                                        continue

                                    joined_this_session += 1
                                    self.joined_groups.append(g_url)
                                    self.save_json_list(JOINED_GROUPS_FILE, self.joined_groups)
                                    found_urls_to_append.append(g_url)
                                    self.log(f"✅ [{joined_this_session}/{max_join}] Đã gửi yêu cầu tham gia: {g_name} ({g_url})")
                                    self.add_or_update_group(
                                        g_url,
                                        group_name=g_name,
                                        group_type="PENDING",
                                        last_status="Mới gửi yêu cầu tham gia",
                                        member_status="⚪ Chờ duyệt TV",
                                        note=f"Tự động tìm kiếm theo từ khóa '{kw}'",
                                        silent=False
                                    )

                                    if joined_this_session < max_join:
                                        wait_sec = random.randint(20, 35)
                                        self.log(f"🛡️ Nghỉ {wait_sec}s trước khi tham gia nhóm tiếp theo...")
                                        time.sleep(wait_sec)
                                else:
                                    composer_check = page.locator(
                                        "div[role='button']:has-text('Bạn viết gì đi'), "
                                        "div[role='button']:has-text('Write something')"
                                    ).first
                                    if composer_check.count() > 0:
                                        self.log(f"ℹ️ Đã là thành viên sẵn của nhóm '{g_name}', thêm vào danh sách đăng.")
                                        if g_url not in self.joined_groups:
                                            self.joined_groups.append(g_url)
                                            self.save_json_list(JOINED_GROUPS_FILE, self.joined_groups)
                                        found_urls_to_append.append(g_url)
                                        self.add_or_update_group(
                                            g_url,
                                            group_name=g_name,
                                            group_type="INSTANT",
                                            last_status="Đã là thành viên",
                                            member_status="Đã tham gia",
                                            note=f"Tự động quét theo từ khóa '{kw}'",
                                            silent=False
                                        )
                            except Exception as e_grp:
                                self.log(f"⚠️ Bỏ qua nhóm {g_url}: {e_grp}")
                                continue

                    if joined_this_session > 0 or found_urls_to_append:
                        self.log("☁️ Đang tự động lưu danh sách nhóm mới lên Tab 'Danh_Sach_Nhom' trên Google Drive...")
                        self.sync_groups_to_google_sheet(context=context, silent=False)

                    context.close()

                if found_urls_to_append:
                    def append_to_ui():
                        current_text = self.txt_groups.get("1.0", "end").strip()
                        existing_lines = [l.strip() for l in current_text.splitlines() if l.strip()]
                        for u in found_urls_to_append:
                            if u not in existing_lines:
                                existing_lines.append(u)
                        self.txt_groups.delete("1.0", "end")
                        self.txt_groups.insert("1.0", "\n".join(existing_lines))
                    self.root.after(0, append_to_ui)

                self.log(f"🏁 Hoàn tất quét nhóm! Đã tham gia mới {joined_this_session} nhóm & cập nhật {len(found_urls_to_append)} link vào danh sách.")
            except Exception as e:
                self.log(f"❌ Lỗi quá trình tìm & tham gia nhóm: {e}")
            finally:
                self.is_posting = False
                self.set_action_buttons_state("normal")

        threading.Thread(target=worker, daemon=True).start()

    # ----------------- DATA ENGINE: PARSER GOOGLE SHEETS -----------------
    def fetch_sheet_data(self):
        url = self.ent_sheet.get().strip()
        if "docs.google.com/spreadsheets" in url and "export?format=csv" not in url:
            m_id = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
            m_gid = re.search(r"[#&?]gid=([0-9]+)", url)
            if m_id:
                s_id = m_id.group(1)
                g_id = m_gid.group(1) if m_gid else "0"
                url = f"https://docs.google.com/spreadsheets/d/{s_id}/export?format=csv&gid={g_id}"

        cache_file = Path(FB_CACHE_DIR) / "fb_sheet_cache.csv"

        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8-sig")
                cache_file.write_text(content, encoding="utf-8")
        except Exception as e:
            self.log(f"⚠️ Mạng chập chờn, sử dụng dữ liệu Cache gần nhất: {e}")
            if cache_file.exists():
                content = cache_file.read_text(encoding="utf-8")
            else:
                raise e

        rows = list(csv.reader(io.StringIO(content)))
        building = ""
        rooms = []
        source_root = Path(self.ent_folder.get().strip())

        for row in rows:
            cells = (row + [""] * 12)[:12]
            no, unit, area, desc, price_usd, price_vnd, service, status, avatar, link_pic, _, _ = cells

            header_keywords = ("HANOI HOME", "WATER FRONT", "LUXURY", "CHEAP", "CHUNG CƯ", "LUMI", "SOLALA")
            no_up = no.strip().upper()
            if (no_up.startswith(header_keywords) or any(k in no_up for k in ["HANOI HOME", "WATER FRONT", "TÔ NGỌC VÂN", "TO NGOC VAN", "TÂY HỒ", "TAY HO", "TỪ HOA", "TU HOA", "NHẬT CHIÊU", "NHAT CHIEU", "ÂU CƠ", "AU CO"])) and not unit.strip():
                building = no.strip()
                continue

            st = status.strip().upper()
            is_valid_status = (st == "NOW" or st == "AVAILABLE")
            if unit.strip() and building and is_valid_status and "CĂN SỐ" not in unit.upper() and "UNIT" not in unit.upper():
                u_str = unit.strip()
                desc_clean = " ".join(desc.split())
                area_clean = normalize_area_text(area, desc_clean)
                ngu_match = re.search(r"(\d+)\s*(?:ngủ|pn|bedroom|br|bed)", desc_clean, re.IGNORECASE)
                tam_match = re.search(r"(\d+)\s*(?:tắm|wc|bath|baths)", desc_clean, re.IGNORECASE)
                so_ngu = ngu_match.group(1) if ngu_match else "1"
                so_tam = tam_match.group(1) if tam_match else "1"

                dia_chi = normalize_building_address(building)

                photo_dir = resolve_room_image_dir(u_str, dia_chi, fallback_root=source_root)
                has_photos = "Chưa có"
                if photo_dir and photo_dir.exists():
                    valid = [p for p in photo_dir.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
                    if len(valid) >= 5:
                        has_photos = f"Đủ ({len(valid)})"
                    elif len(valid) > 0:
                        has_photos = f"Có ({len(valid)})"

                rooms.append({
                    "unit": u_str,
                    "building": dia_chi,
                    "full_building": building,
                    "area": area_clean,
                    "desc": desc_clean,
                    "so_ngu": so_ngu,
                    "so_tam": so_tam,
                    "price": price_vnd.strip(),
                    "price_vnd": price_vnd.strip(),
                    "price_usd": price_usd.strip(),
                    "status": status.strip(),
                    "has_photos": has_photos,
                    "photo_dir": str(photo_dir) if photo_dir else ""
                })

        return rooms

    def trigger_check_sheet(self):
        def worker():
            try:
                self.log("Đang đồng bộ dữ liệu từ Google Sheets...")
                self.rooms_data = self.fetch_sheet_data()
                self.root.after(0, self.render_rooms_tree)
                self.log(f"✅ Đồng bộ thành công! Có {len(self.rooms_data)} căn phòng trống sẵn sàng.")
            except Exception as e:
                self.log(f"❌ Lỗi tải Google Sheets: {e}")
        threading.Thread(target=worker, daemon=True).start()

    # ----------------- QUẢN LÝ ẨN / HIỆN CĂN VÀ TÒA NHÀ TRỐNG -----------------
    def make_room_key(self, unit, building):
        return f"{str(unit).strip().upper()}@@@{str(building).strip().upper()}"

    def is_room_hidden(self, unit, building):
        b_up = str(building).strip().upper()
        r_key = self.make_room_key(unit, building)
        return (b_up in self.hidden_buildings) or (r_key in self.hidden_rooms)

    def hide_selected_room(self):
        room = self.get_selected_room()
        if not room:
            messagebox.showinfo("Chưa chọn căn", "Vui lòng bấm chọn một căn trong bảng danh sách.")
            return
        r_key = self.make_room_key(room["unit"], room["building"])
        self.hidden_rooms.add(r_key)
        save_hidden_rooms_config(self.hidden_rooms, self.hidden_buildings)
        self.log(f"👁️ Đã ẩn Căn {room['unit']} ({room['building']}) khỏi danh sách hiển thị và đăng bài.")
        self.render_rooms_tree()

    def hide_selected_building(self):
        room = self.get_selected_room()
        if not room:
            messagebox.showinfo("Chưa chọn căn", "Vui lòng bấm chọn một căn thuộc tòa nhà bạn muốn ẩn.")
            return
        bld = room["building"]
        b_up = str(bld).strip().upper()
        self.hidden_buildings.add(b_up)
        save_hidden_rooms_config(self.hidden_rooms, self.hidden_buildings)
        self.log(f"🏢 Đã ẩn toàn bộ các căn thuộc tòa '{bld}' khỏi danh sách hiển thị và đăng bài.")
        self.render_rooms_tree()

    def unhide_selected_room(self):
        room = self.get_selected_room()
        if not room:
            messagebox.showinfo("Chưa chọn căn", "Vui lòng bấm chọn một căn để bỏ ẩn.")
            return
        r_key = self.make_room_key(room["unit"], room["building"])
        b_up = str(room["building"]).strip().upper()
        removed = False
        if r_key in self.hidden_rooms:
            self.hidden_rooms.remove(r_key)
            removed = True
        if b_up in self.hidden_buildings:
            self.hidden_buildings.remove(b_up)
            removed = True
        if removed:
            save_hidden_rooms_config(self.hidden_rooms, self.hidden_buildings)
            self.log(f"🔓 Đã bỏ ẩn cho Căn {room['unit']} ({room['building']}).")
            self.render_rooms_tree()
        else:
            messagebox.showinfo("Thông báo", f"Căn {room['unit']} ({room['building']}) hiện không nằm trong danh sách ẩn.")

    def reset_all_hidden(self):
        if not self.hidden_rooms and not self.hidden_buildings:
            messagebox.showinfo("Thông báo", "Hiện không có căn hay tòa nào bị ẩn.")
            return
        total_hidden = len(self.hidden_rooms) + len(self.hidden_buildings)
        if messagebox.askyesno("Xác nhận bỏ ẩn", f"Bạn có chắc muốn BỎ ẨN TẤT CẢ ({len(self.hidden_rooms)} căn và {len(self.hidden_buildings)} tòa đã ẩn)?"):
            self.hidden_rooms.clear()
            self.hidden_buildings.clear()
            save_hidden_rooms_config(self.hidden_rooms, self.hidden_buildings)
            self.log("🔄 Đã bỏ ẩn toàn bộ căn và tòa nhà! Tất cả đều đã hiển thị trở lại.")
            self.render_rooms_tree()

    def setup_tree_context_menu(self):
        self.tree_menu = tk.Menu(self.root, tearoff=0)
        self.tree_menu.add_command(label="👁️ Ẩn căn này", command=self.hide_selected_room)
        self.tree_menu.add_command(label="🏢 Ẩn toàn bộ căn thuộc tòa này", command=self.hide_selected_building)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="🔓 Bỏ ẩn căn này", command=self.unhide_selected_room)
        self.tree_menu.add_command(label="🔄 Bỏ ẩn tất cả căn & tòa", command=self.reset_all_hidden)

    def show_tree_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            self.on_room_select(None)
            self.tree_menu.post(event.x_root, event.y_root)

    def render_rooms_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.rooms_data:
            if hasattr(self, "lbl_room_count_stat"):
                self.lbl_room_count_stat.config(text="📊 Hiển thị: 0 / 0 căn")
            return

        # Nạp danh sách tòa nhà vào Combobox lọc nếu có thay đổi
        all_buildings = sorted(list({r["building"] for r in self.rooms_data if r.get("building")}))
        combo_values = ["Tất cả tòa nhà"] + all_buildings
        if hasattr(self, "cmb_filter_building"):
            curr_bld = self.cmb_filter_building.get()
            self.cmb_filter_building["values"] = combo_values
            if curr_bld not in combo_values:
                self.cmb_filter_building.set("Tất cả tòa nhà")

        selected_bld = self.cmb_filter_building.get() if hasattr(self, "cmb_filter_building") else "Tất cả tòa nhà"
        show_hidden = self.chk_show_hidden.get() if hasattr(self, "chk_show_hidden") else False

        total_rooms = len(self.rooms_data)
        hidden_count = 0
        shown_count = 0

        for r in self.rooms_data:
            is_hidden = self.is_room_hidden(r["unit"], r["building"])
            if is_hidden:
                hidden_count += 1

            if selected_bld != "Tất cả tòa nhà" and r["building"] != selected_bld:
                continue

            if is_hidden and not show_hidden:
                continue

            unit_label = f"🔒 [ẨN] {r['unit']}" if is_hidden else r["unit"]

            self.tree.insert("", "end", values=(
                unit_label,
                r["building"],
                r["area"] or "-",
                r["desc"],
                r["price_usd"] or "-",
                r["price"],
                r["has_photos"]
            ))
            shown_count += 1

        if hasattr(self, "lbl_room_count_stat"):
            self.lbl_room_count_stat.config(
                text=f"📊 Hiển thị: {shown_count}/{total_rooms} căn (Đang ẩn: {hidden_count} căn)"
            )

        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])
            self.on_room_select(None)

    def get_selected_room(self):
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0], "values")
        if vals:
            unit_raw, bld = str(vals[0]), str(vals[1])
            unit = unit_raw.replace("🔒 [ẨN] ", "").strip()
            return next((r for r in self.rooms_data if r["unit"] == unit and r["building"] == bld), None)
        return None

    def on_room_select(self, event, spin=False):
        room = self.get_selected_room()
        if not room:
            return
        mode = self.cmb_template.get()
        msg = build_post_message(room, template_mode=mode, spin=spin)
        self.txt_message.delete("1.0", "end")
        self.txt_message.insert("1.0", msg)

        target_folder = room.get("photo_dir") or str(resolve_room_image_dir(room["unit"], room["building"], self.ent_folder.get().strip()) or "")
        if target_folder and Path(target_folder).exists():
            room["photo_dir"] = target_folder
            self.ent_folder.delete(0, "end")
            self.ent_folder.insert(0, target_folder)
            valid = [p for p in Path(target_folder).iterdir() if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
            count = len(valid)
            color = "#16a34a" if count >= 5 else ("#ca8a04" if count > 0 else "#dc2626")
            if hasattr(self, "lbl_room_photo_info"):
                self.lbl_room_photo_info.config(
                    text=f"📁 Căn {room['unit']} ({room['building']}): {target_folder} [{room.get('has_photos', f'{count} ảnh')}]",
                    foreground=color
                )
        else:
            if hasattr(self, "lbl_room_photo_info"):
                self.lbl_room_photo_info.config(
                    text=f"📁 Căn {room['unit']} ({room['building']}): ⚠️ Chưa có kho ảnh (Bấm 'Chọn kho ảnh cho căn này')",
                    foreground="#dc2626"
                )

    def trigger_choose_room_photo_dir(self):
        room = self.get_selected_room()
        if not room:
            messagebox.showinfo("Chưa chọn căn", "Vui lòng bấm chọn một căn trong bảng danh sách phía trên trước.")
            return

        unit = room.get("unit", "")
        building = room.get("building", "")
        init_dir = room.get("photo_dir") or self.ent_folder.get().strip()
        if not init_dir or not Path(init_dir).exists():
            init_dir = str(DATA_BASE_DIR) if DATA_BASE_DIR.exists() else str(APP_BASE_DIR)

        chosen_dir = filedialog.askdirectory(
            title=f"Chọn thư mục ảnh cho Căn {unit} - {building}",
            initialdir=init_dir
        )
        if not chosen_dir:
            return

        p_dir = Path(chosen_dir)
        valid_files = [f for f in p_dir.iterdir() if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
        count = len(valid_files)
        has_photos = f"Đủ ({count})" if count >= 5 else (f"Có ({count})" if count > 0 else "Chưa có (0)")

        room["photo_dir"] = str(p_dir)
        room["has_photos"] = has_photos

        save_custom_room_photo(unit, building, str(p_dir))
        save_custom_room_photo(unit, room.get("full_building", building), str(p_dir))

        sel = self.tree.selection()
        if sel:
            self.tree.item(sel[0], values=(
                room["unit"],
                room["building"],
                room["area"] or "-",
                room["desc"],
                room["price_usd"] or "-",
                room["price"],
                room["has_photos"]
            ))

        color = "#16a34a" if count >= 5 else ("#ca8a04" if count > 0 else "#dc2626")
        if hasattr(self, "lbl_room_photo_info"):
            self.lbl_room_photo_info.config(
                text=f"📁 Căn {unit} ({building}): {p_dir} [{has_photos}]",
                foreground=color
            )
        self.ent_folder.delete(0, "end")
        self.ent_folder.insert(0, str(p_dir))

        self.log(f"✅ Đã cập nhật thành công kho ảnh cho Căn {unit} - {building}: '{p_dir}' ({count} ảnh hợp lệ).")

    def trigger_open_room_photo_dir(self):
        room = self.get_selected_room()
        if not room:
            messagebox.showinfo("Chưa chọn căn", "Vui lòng bấm chọn một căn trong bảng danh sách phía trên trước.")
            return
        photo_dir = room.get("photo_dir")
        if photo_dir and Path(photo_dir).exists():
            os.startfile(photo_dir)
        else:
            messagebox.showwarning("Chưa có thư mục", f"Căn {room.get('unit')} hiện chưa có thư mục ảnh hợp lệ. Vui lòng bấm 'Chọn kho ảnh cho căn này' để cài đặt.")

    # ----------------- IMAGE ENGINE: KÍCH THƯỚC GỐC (5-7 ẢNH) -----------------
    def prepare_room_photos(self, unit_id, source_root=None, max_photos=DEFAULT_MAX_PHOTOS, building=""):
        target_dir = None
        u_str = str(unit_id).strip().upper()

        if source_root:
            p_source = Path(source_root)
            if p_source.exists():
                u_digits = re.findall(r"\d+", u_str)
                u_num = u_digits[0] if u_digits else ""
                if (
                    p_source.name.strip().upper() == u_str
                    or f"R{u_str}" in p_source.name.upper()
                    or f" {u_str} " in f" {p_source.name} "
                    or u_str in p_source.name.upper()
                    or (u_num and f"FLOOR{u_num}" in p_source.name.replace(" ", "").upper())
                ):
                    target_dir = p_source
                else:
                    for item in p_source.iterdir():
                        if item.is_dir():
                            item_up = item.name.strip().upper()
                            if (
                                item_up == u_str
                                or f"R{u_str}" in item_up
                                or f" {u_str} " in f" {item.name} "
                                or u_str.lower() in item.name.lower()
                                or (u_num and f"FLOOR{u_num}" in item_up.replace(" ", ""))
                            ):
                                target_dir = item
                                break
                    if not target_dir and any(f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} for f in p_source.iterdir() if f.is_file()):
                        target_dir = p_source

        if not target_dir:
            resolved = resolve_room_image_dir(unit_id, building, fallback_root=source_root)
            if resolved and resolved.exists():
                target_dir = resolved

        if not target_dir or not target_dir.exists():
            self.log(f"⚠️ Thư mục ảnh không tồn tại cho căn {unit_id} ({building}): {source_root}")
            return []

        valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
        image_files = [p for p in target_dir.iterdir() if p.suffix.lower() in valid_exts]

        if not image_files:
            self.log(f"⚠️ Không tìm thấy ảnh cho căn {unit_id} tại {target_dir}")
            return []

        sorted_files = select_and_sort_photos(image_files, max_photos=max_photos)
        photo_paths = [str(p) for p in sorted_files]
        self.log(f"🖼️ Chuẩn bị {len(photo_paths)} ảnh gốc từ '{target_dir.name}' (Livingroom -> Kitchen -> Bedroom -> Bathroom).")
        return photo_paths

    # ----------------- LẤY LINK BÀI VỪA ĐĂNG & PHÂN LOẠI NHÓM KHÔNG DUYỆT -----------------
    def extract_group_name_and_post_url(self, page, group_url, unit_id=""):
        base_group = normalize_group_base_url(group_url)
        group_id_match = re.search(r"/groups/([^/?#]+)", base_group)
        group_slug = group_id_match.group(1) if group_id_match else ""

        # 1. Trích xuất Tên Nhóm từ Header h1
        group_name = group_url
        try:
            h1_loc = page.locator("h1 a, h1 span").first
            if h1_loc.count() > 0:
                txt = h1_loc.inner_text(timeout=3000).strip()
                if txt and "Facebook" not in txt:
                    group_name = txt
        except Exception:
            pass

        time.sleep(3.0)

        # 2. Kiểm tra dấu hiệu rõ ràng của bài viết chờ phê duyệt (Pending / Quản lý bài viết)
        is_pending = False

        if "pending_posts" in page.url or "manage_posts" in page.url:
            is_pending = True

        if not is_pending:
            try:
                # Kiểm tra thông báo toast / alert sau khi bấm Đăng
                alerts = page.locator("div[role='alert'], div[aria-live='polite'], div[role='status']").all()
                for al in alerts:
                    try:
                        al_txt = al.inner_text(timeout=1000).lower()
                        if any(k in al_txt for k in [
                            "chờ", "pending", "phê duyệt", "quản trị viên", "quản lý bài viết",
                            "đã được gửi", "submitted", "admin approval", "xem xét"
                        ]):
                            is_pending = True
                            break
                    except Exception:
                        continue
            except Exception:
                pass

        if not is_pending:
            try:
                # Kiểm tra các banner / nhãn trạng thái trên giao diện nhóm
                pending_indicators = page.locator(
                    "text=/quản lý bài viết|đang chờ quản trị viên phê duyệt|chờ.*phê duyệt|pending approval|submitted to.*admin|bài viết của bạn đã được gửi|bài viết đang chờ|1 bài viết đang chờ/i"
                ).first
                if pending_indicators.count() > 0 and pending_indicators.is_visible():
                    is_pending = True
            except Exception:
                pass

        if is_pending:
            post_status = "Đang chờ phê duyệt"
            post_url = base_group
            self.log(f"🟡 Nhóm '{group_name}' yêu cầu phê duyệt: Bài đã được gửi vào mục 'Quản lý bài viết - Đang chờ quản trị viên phê duyệt'.")
            return group_name, post_url, post_status

        # 3. Tìm link bài đăng công khai thực sự trên Bảng tin (Feed) của Nhóm
        matched_url = None
        try:
            # Ưu tiên 1: Link "Xem bài viết" từ Toast thông báo
            toast_links = page.locator(
                "div[role='alert'] a, div[aria-live='polite'] a, a:has-text('Xem bài viết'), a:has-text('View post')"
            ).all()
            for tl in toast_links:
                try:
                    href = tl.get_attribute("href") or ""
                    if "/groups/" in href and ("/posts/" in href or "/permalink/" in href):
                        if "pending_posts" in href:
                            is_pending = True
                            break
                        clean_href = href.split("?")[0]
                        if clean_href.startswith("/"):
                            clean_href = "https://www.facebook.com" + clean_href
                        matched_url = clean_href
                        break
                except Exception:
                    continue

            if is_pending:
                return group_name, base_group, "Đang chờ phê duyệt"

            # Ưu tiên 2: Tìm bài viết mới có mã căn trong Bảng tin (Feed)
            if not matched_url:
                feed_container = page.locator("div[role='feed']").first
                search_scope = feed_container if feed_container.count() > 0 else page

                group_post_anchors = search_scope.locator(
                    "a[href*='/groups/'][href*='/posts/'], a[href*='/groups/'][href*='/permalink/']"
                ).all()

                valid_post_links = []
                for a in group_post_anchors[:20]:
                    try:
                        href = a.get_attribute("href") or ""
                        if not href or "/groups/" not in href or "pending_posts" in href:
                            continue
                        clean_h = href.split("?")[0]
                        if clean_h.startswith("/"):
                            clean_h = "https://www.facebook.com" + clean_h
                        if clean_h not in [v[0] for v in valid_post_links]:
                            valid_post_links.append((clean_h, a))
                    except Exception:
                        continue

                for c_url, anchor in valid_post_links:
                    try:
                        p_card = anchor.locator("xpath=./ancestor::div[@role='article']").first
                        if p_card.count() > 0:
                            parent_text = p_card.inner_text().upper()
                            # Khớp chính xác mã căn vừa đăng (ví dụ '402', '157 NHẬT CHIÊU') hoặc nhãn 'VỪA XONG'
                            if unit_id and str(unit_id).upper() in parent_text:
                                matched_url = c_url
                                break
                            if "VỪA XONG" in parent_text or "JUST NOW" in parent_text:
                                matched_url = c_url
                                break
                    except Exception:
                        continue

        except Exception:
            pass

        # 4. ĐÁNH GIÁ CHỐT:
        # Nếu TÌM THẤY bài viết công khai trên Feed có mã căn hoặc vừa xong -> Chắc chắn "Đã đăng" (🟢 ĐĂNG NGAY)
        # Nếu KHÔNG TÌM THẤY bài trên Feed -> Bài viết đã vào hàng chờ duyệt (Quản lý bài viết) -> Chắc chắn "Đang chờ phê duyệt" (🟡 CHỜ DUYỆT)
        if matched_url:
            post_status = "Đã đăng"
            post_url = matched_url
            self.log(f"🟢 Nhóm '{group_name}' duyệt tự động: Bài đã hiển thị công khai trên Feed nhóm!")
        else:
            post_status = "Đang chờ phê duyệt"
            post_url = base_group
            self.log(f"🟡 Nhóm '{group_name}' kiểm duyệt bài: Bài vào mục 'Quản lý bài viết - Đang chờ quản trị viên phê duyệt'.")

        if post_url and "pending_posts" in post_url:
            post_url = base_group

        return group_name, post_url, post_status

    # ----------------- GHI BÁO CÁO LÊN ĐẦU BẢNG (DÒNG 5 - NGAY TRÊN BÀI ĐĂNG CŨ) -----------------
    def insert_rows_above_row5(self, sheet_page, num_rows_to_insert):
        if num_rows_to_insert <= 0:
            return True

        name_box = sheet_page.locator("#t-name-box").first
        if name_box.count() == 0:
            return False

        # Thử chèn một lần toàn bộ số hàng (chọn 5:(4+N) rồi chèn N hàng lên trên)
        try:
            name_box.click()
            time.sleep(0.3)
            sheet_page.keyboard.press("Control+A")
            sheet_page.keyboard.type(f"5:{4 + num_rows_to_insert}")
            sheet_page.keyboard.press("Enter")
            time.sleep(0.5)

            insert_menu = sheet_page.locator(
                "#docs-insert-menu, "
                "div[role='menuitem']:has-text('Chèn'), "
                "div[role='menuitem']:has-text('Insert')"
            ).first
            if insert_menu.count() > 0:
                insert_menu.click()
                time.sleep(0.4)
                rows_item = sheet_page.locator(
                    ".goog-menuitem:has-text('Hàng'), "
                    ".goog-menuitem:has-text('Rows')"
                ).first
                if rows_item.count() > 0:
                    rows_item.hover()
                    time.sleep(0.4)
                    above_item = sheet_page.locator(
                        ".goog-menuitem:has-text('lên trên'), "
                        ".goog-menuitem:has-text('above')"
                    ).first
                    if above_item.count() > 0:
                        above_item.click()
                        time.sleep(1.0)
                        return True
        except Exception:
            pass

        # Dự phòng: lặp từng hàng nếu thao tác khối không thành công
        name_box.click()
        time.sleep(0.3)
        sheet_page.keyboard.press("Control+A")
        sheet_page.keyboard.type("A5")
        sheet_page.keyboard.press("Enter")
        time.sleep(0.6)

        for _ in range(num_rows_to_insert):
            inserted = False
            insert_menu = sheet_page.locator(
                "#docs-insert-menu, "
                "div[role='menuitem']:has-text('Chèn'), "
                "div[role='menuitem']:has-text('Insert')"
            ).first
            if insert_menu.count() > 0:
                try:
                    insert_menu.click()
                    time.sleep(0.4)
                    rows_item = sheet_page.locator(
                        ".goog-menuitem:has-text('Hàng'), "
                        ".goog-menuitem:has-text('Rows'), "
                        ".goog-menuitem:has-text('Row')"
                    ).first
                    if rows_item.count() > 0:
                        rows_item.hover()
                        time.sleep(0.35)
                        above_item = sheet_page.locator(
                            ".goog-menuitem:has-text('lên trên'), "
                            ".goog-menuitem:has-text('above')"
                        ).first
                        if above_item.count() > 0:
                            above_item.click()
                            time.sleep(0.5)
                            inserted = True
                except Exception:
                    pass

            if not inserted:
                sheet_page.keyboard.press("Alt+i")
                time.sleep(0.35)
                sheet_page.keyboard.press("r")
                time.sleep(0.5)

        return True

    def write_reports_to_google_sheet(self, context, records):
        if not records:
            return

        local_csv = Path(FB_CACHE_DIR) / "fb_post_reports.csv"
        file_exists = local_csv.exists()
        with open(local_csv, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["STT", "Tên Nhóm", "Bài Đăng", "Link", "Ngày đăng", "Status"])
            for idx, r in enumerate(records, start=1):
                clean_u = str(r.get("post_url", "")).split("?")[0]
                clean_u = re.sub(r"/pending_posts(?:/.*)?/?$", "/", clean_u)
                writer.writerow([idx, r["group_name"], r["post_label"], clean_u, r["date_str"], r["status"]])

        report_url = self.ent_report_sheet.get().strip()
        if not report_url or "docs.google.com/spreadsheets" not in report_url:
            self.log("⚠️ Link Google Sheet báo cáo không hợp lệ, đã lưu tạm vào CSV máy tính.")
            return

        self.log(f"📊 Đang mở Google Sheet báo cáo để chèn {len(records)} dòng mới lên đầu bảng (Dòng 5, ngay trên bài cũ)...")
        sheet_page = context.new_page()
        try:
            sheet_page.goto(report_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(5.0)

            if "accounts.google.com" in sheet_page.url:
                self.log("🔐 Chrome Profile chưa đăng nhập Google! Mời bạn đăng nhập Google trên tab vừa mở (chờ tối đa 180s)...")
                logged_in = False
                for _ in range(180):
                    if "accounts.google.com" not in sheet_page.url and "docs.google.com/spreadsheets/d/" in sheet_page.url:
                        logged_in = True
                        self.log("✅ Đã đăng nhập Google thành công! Tiếp tục chèn báo cáo...")
                        time.sleep(3.0)
                        break
                    time.sleep(1.0)
                if not logged_in:
                    self.log("⚠️ Hết thời gian chờ đăng nhập Google (180s). Báo cáo đã được lưu an toàn tại CSV máy tính.")
                    return

            # Đảm bảo chắc chắn đang thao tác trên thẻ Báo cáo (Trang tính 1)
            tab1_rect = sheet_page.evaluate("""() => {
                const tabs = Array.from(document.querySelectorAll('.docs-sheet-tab'));
                for (const t of tabs) {
                    const txt = (t.innerText || '').trim();
                    if (txt.includes('Trang tính1') || txt.includes('Trang tính 1') || txt.includes('Sheet1') || txt.includes('Báo cáo')) {
                        const r = t.getBoundingClientRect();
                        return { found: true, x: r.x + r.width/2, y: r.y + r.height/2 };
                    }
                }
                return { found: false };
            }""")
            if tab1_rect.get("found"):
                sheet_page.mouse.click(tab1_rect["x"], tab1_rect["y"])
                time.sleep(2.0)

            total_insert_rows = len(records)
            self.log(f"↕️ Đang chèn {total_insert_rows} hàng trống tại đầu bảng (Dòng 5) để đẩy bài cũ xuống dưới...")
            self.insert_rows_above_row5(sheet_page, total_insert_rows)

            name_box = sheet_page.locator("#t-name-box").first
            if name_box.count() > 0:
                name_box.click()
                time.sleep(0.3)
                sheet_page.keyboard.press("Control+A")
                sheet_page.keyboard.type("A5")
                sheet_page.keyboard.press("Enter")
                time.sleep(0.8)

            tsv_lines = []
            for i, rec in enumerate(records, start=1):
                clean_g = str(rec.get("group_name", "")).replace("\t", " ").replace("\n", " ").strip()
                clean_l = str(rec.get("post_label", "")).replace("\t", " ").replace("\n", " ").strip()
                clean_u = str(rec.get("post_url", "")).replace("\t", " ").replace("\n", " ").strip()
                clean_d = str(rec.get("date_str", "")).replace("\t", " ").replace("\n", " ").strip()
                clean_s = str(rec.get("status", "")).replace("\t", " ").replace("\n", " ").strip()
                clean_u = re.sub(r"/pending_posts(?:/.*)?/?$", "/", clean_u)
                tsv_lines.append(f"{i}\t{clean_g}\t{clean_l}\t{clean_u}\t{clean_d}\t{clean_s}")

            tsv_text = "\n".join(tsv_lines)
            pyperclip.copy(tsv_text)
            time.sleep(0.3)
            sheet_page.keyboard.press("Control+V")
            time.sleep(2.5)
            self.log(f"✅ Đã dán xong {len(records)} bài mới lên đầu bảng tại DÒNG 5 (ngay trên bài đăng cũ)!")
        except Exception as e:
            self.log(f"⚠️ Không thể tự ghi trực tiếp lên Google Sheet ({e}). Dữ liệu đã được lưu an toàn tại: {local_csv}")
        finally:
            try:
                sheet_page.close()
            except Exception:
                pass

    # ----------------- AUTOMATION ENGINE: FACEBOOK GROUPS + KIỂM TRA BỊ KÍCH -----------------
    def execute_post_to_fb_groups(self, manual_preview_text, image_paths, room):
        raw_groups = self.txt_groups.get("1.0", "end").strip().splitlines()
        group_urls = [g.split("#")[0].strip() for g in raw_groups if g.strip().startswith("http")]

        if not group_urls:
            self.log("⚠️ Chưa nhập link Group Facebook nào hợp lệ (phải bắt đầu bằng https://).")
            return

        os.makedirs(FB_CHROME_PROFILE_DIR, exist_ok=True)
        auto_submit = self.chk_auto_click_post.get()
        auto_report = self.chk_auto_report.get()
        auto_rejoin = self.chk_auto_rejoin.get()
        template_mode = self.cmb_template.get()
        posted_records = []

        short_bld = format_report_building_short(room.get("building", ""))
        area_tag = f" ({room['area']})" if room.get("area") else ""
        post_label = f"{room.get('unit', '').strip()} - {short_bld}{area_tag}".strip(" -")
        today_str = datetime.now().strftime("%d-%m-%Y").lstrip("0").replace("-0", "-")

        self.log(f"🌐 Mở Chrome Profile riêng cho FB Groups ({len(group_urls)} nhóm | Mẫu: {template_mode})...")

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=FB_CHROME_PROFILE_DIR,
                channel="chrome",
                headless=False,
                viewport={"width": 1280, "height": 850},
                ignore_default_args=["--enable-automation"],
                args=["--disable-blink-features=AutomationControlled", "--disable-notifications"]
            )
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
            page = context.pages[0] if context.pages else context.new_page()

            for idx, group_url in enumerate(group_urls, start=1):
                try:
                    self.log(f"➡️ [{idx}/{len(group_urls)}] Đang kiểm tra & mở nhóm: {group_url}")
                    page.goto(group_url, wait_until="domcontentloaded", timeout=45000)
                    time.sleep(random.uniform(3.5, 5.5))

                    if "login" in page.url or page.locator("input[name='email']").count() > 0:
                        self.log("🔐 Chưa đăng nhập Facebook! Vui lòng đăng nhập trên cửa sổ Chrome vừa mở (chờ tối đa 180s)...")
                        fb_ok = False
                        for _ in range(180):
                            if "login" not in page.url and page.locator("input[name='email']").count() == 0:
                                fb_ok = True
                                self.log("✅ Đã nhận diện đăng nhập Facebook thành công!")
                                time.sleep(2.5)
                                break
                            time.sleep(1.0)
                        if not fb_ok:
                            self.log("⚠️ Hết thời gian chờ đăng nhập Facebook (180s). Bỏ qua nhóm này.")
                            continue
                        if "/groups/" not in page.url:
                            page.goto(group_url, wait_until="domcontentloaded", timeout=45000)
                            time.sleep(3.0)

                    kicked_join_btn = page.locator(
                        "div[role='button']:has-text('Tham gia nhóm'), "
                        "div[role='button']:has-text('Join group'), "
                        "div[role='button']:has-text('Join Group'), "
                        "[aria-label*='Tham gia nhóm'], "
                        "[aria-label*='Join group']"
                    ).first

                    blocked_banner = page.locator("text=/nội dung này hiện không hiển thị|content isn't available|bị chặn|suspended/i").first

                    if blocked_banner.count() > 0:
                        self.log(f"🚫 Nhóm {group_url} không khả dụng hoặc đã chặn tài khoản -> Xóa khỏi Kho Nhóm Sạch & bỏ qua.")
                        self.remove_from_clean_groups(group_url)
                        if auto_rejoin:
                            self.find_similar_replacement_group(page, set(group_urls))
                        continue

                    if kicked_join_btn.count() > 0 and kicked_join_btn.is_visible():
                        self.log(f"⚠️ Phát hiện tài khoản đã bị kích ra khỏi nhóm: {group_url}!")
                        self.remove_from_clean_groups(group_url)
                        if auto_rejoin:
                            try:
                                kicked_join_btn.click()
                                time.sleep(2.5)
                                q_dlg = page.locator("div[role='dialog']:has-text('Trả lời câu hỏi'), div[role='dialog']:has-text('Answer questions')").first
                                if q_dlg.count() > 0:
                                    close_b = page.locator("div[role='dialog'] [aria-label='Đóng'], div[role='dialog'] [aria-label='Close']").first
                                    if close_b.count() > 0:
                                        close_b.click()
                                    self.log("↪️ Nhóm yêu cầu trả lời câu hỏi khi xin vào lại -> Chuyển sang tìm nhóm tương tự thay thế...")
                                    self.find_similar_replacement_group(page, set(group_urls))
                                else:
                                    self.log("🔄 Đã tự động bấm GỬI YÊU CẦU XIN VÀO LẠI nhóm này (chờ Admin duyệt) & tìm thêm nhóm tương tự!")
                                    self.find_similar_replacement_group(page, set(group_urls))
                            except Exception:
                                pass
                        continue

                    pending_member_btn = page.locator(
                        "div[role='button']:has-text('Hủy yêu cầu'), "
                        "div[role='button']:has-text('Cancel request')"
                    ).first
                    if pending_member_btn.count() > 0 and pending_member_btn.is_visible():
                        self.log(f"⏳ Nhóm {group_url} đang chờ Admin duyệt thành viên -> Bỏ qua sang nhóm kế tiếp.")
                        continue

                    discussion_tab = page.locator("a[role='tab']:has-text('Thảo luận'), a[role='tab']:has-text('Discussion')").first
                    if discussion_tab.count() > 0:
                        try:
                            discussion_tab.click(timeout=3000)
                            time.sleep(2)
                        except Exception:
                            pass

                    composer_btn = page.locator(
                        "div[role='button']:has-text('Bạn viết gì đi'), "
                        "div[role='button']:has-text('Write something'), "
                        "div[role='button']:has-text('Tạo bài viết'), "
                        "div[role='button']:has-text('Create a public post'), "
                        "div[role='button']:has-text('Create a post'), "
                        "div[role='button']:has-text('Bạn đang nghĩ gì'), "
                        "[aria-label*='Tạo bài viết'], "
                        "[aria-label*='Write something']"
                    ).first

                    if composer_btn.count() == 0:
                        self.log(f"⏳ Nhóm {group_url} chưa mở khung đăng bài (có thể bị tắt quyền đăng hoặc chờ duyệt). Bỏ qua.")
                        continue

                    page.mouse.wheel(0, random.randint(200, 380))
                    time.sleep(1.2)

                    composer_btn.wait_for(state="visible", timeout=15000)
                    composer_btn.click()
                    time.sleep(random.uniform(2.0, 3.0))

                    if idx == 1 and manual_preview_text:
                        final_text = manual_preview_text
                    else:
                        final_text = build_post_message(room, template_mode=template_mode, spin=True)

                    textbox = page.locator("div[role='dialog'] div[role='textbox']").first
                    textbox.wait_for(state="visible", timeout=10000)
                    textbox.click()
                    time.sleep(0.5)
                    pyperclip.copy(final_text)
                    page.keyboard.press("Control+V")
                    time.sleep(1.5)

                    if image_paths:
                        self.log(f"📸 Đang nạp {len(image_paths)} ảnh gốc lên bài viết...")
                        file_input = page.locator("div[role='dialog'] input[type='file']").first
                        if file_input.count() == 0:
                            photo_btn = page.locator(
                                "div[role='dialog'] [aria-label*='Ảnh/video'], "
                                "div[role='dialog'] [aria-label*='Photo/video'], "
                                "div[role='dialog'] [aria-label*='Ảnh'], "
                                "div[role='dialog'] [aria-label*='Photo'], "
                                "div[role='dialog'] div[role='button']:has-text('Ảnh'), "
                                "div[role='dialog'] div[role='button']:has-text('Photo')"
                            ).first
                            if photo_btn.count() > 0:
                                photo_btn.click()
                                time.sleep(1.2)
                            file_input = page.locator("div[role='dialog'] input[type='file']").first

                        if file_input.count() > 0:
                            file_input.set_input_files(image_paths)
                            wait_upload = max(5.0, len(image_paths) * 1.5)
                            self.log(f"⏳ Chờ Facebook tải xong preview {len(image_paths)} ảnh ({wait_upload:.1f}s)...")
                            time.sleep(wait_upload)
                        else:
                            self.log("⚠️ Không tìm thấy ô tải ảnh trong hộp thoại Facebook.")

                    if auto_submit:
                        post_btn = page.locator(
                            "div[role='dialog'] div[aria-label='Đăng'], "
                            "div[role='dialog'] div[aria-label='Post'], "
                            "div[role='dialog'] div[role='button']:has-text('Đăng'), "
                            "div[role='dialog'] div[role='button']:has-text('Post')"
                        ).last
                        post_btn.wait_for(state="visible", timeout=12000)
                        for _ in range(30):
                            if post_btn.get_attribute("aria-disabled") != "true":
                                break
                            time.sleep(1.0)
                        post_btn.click()
                        self.log(f"✅ Đã bấm ĐĂNG thành công tại nhóm [{idx}/{len(group_urls)}]!")
                        try:
                            page.locator("div[role='dialog']").wait_for(state="hidden", timeout=25000)
                        except Exception:
                            pass
                        time.sleep(4.0)
                    else:
                        self.log(f"📝 Đã điền sẵn bài & ảnh tại nhóm [{idx}]. Mời bạn kiểm tra và bấm Đăng trên Chrome (chờ 25s)...")
                        time.sleep(25)

                    g_name, p_url, p_status = self.extract_group_name_and_post_url(page, group_url, unit_id=room.get("unit", ""))
                    self.log(f"🔗 Ghi nhận báo cáo: {g_name} | {post_label} | {p_status} -> {p_url}")

                    if p_status == "Đã đăng":
                        self.add_or_update_group(
                            group_url,
                            group_name=g_name,
                            group_type="INSTANT",
                            last_status="Đã đăng",
                            member_status="Đã là thành viên",
                            note="Đăng ngay không kiểm duyệt"
                        )
                    elif p_status == "Đang chờ phê duyệt":
                        self.add_or_update_group(
                            group_url,
                            group_name=g_name,
                            group_type="PENDING",
                            last_status="Đang chờ phê duyệt",
                            member_status="Đã là thành viên",
                            note="Bài đăng vào mục Chờ duyệt (Pending)"
                        )

                    posted_records.append({
                        "group_name": g_name,
                        "post_label": post_label,
                        "post_url": p_url,
                        "date_str": today_str,
                        "status": p_status,
                    })

                    if idx < len(group_urls):
                        delay = random.randint(45, 90)
                        self.log(f"🛡️ Nghỉ an toàn {delay} giây trước khi sang nhóm tiếp theo...")
                        time.sleep(delay)

                except Exception as e:
                    self.log(f"❌ Lỗi tại nhóm {group_url}: {e}")
                    continue

            if auto_report and posted_records:
                self.write_reports_to_google_sheet(context, posted_records)
                self.sync_groups_to_google_sheet(context=context, silent=True)

            self.log("🏁 Hoàn tất phiên đăng bài & phân loại nhóm Facebook Groups!")
            context.close()

    # ----------------- TỰ ĐỘNG DUYỆT NHÓM & ĐĂNG ĐỦ 10 BÀI BÁO CÁO (AN TOÀN) -----------------
    def get_candidate_rooms_for_auto(self):
        candidates = []
        for r in self.rooms_data:
            st = r.get("status", "").strip().upper()
            if st not in ("NOW", "AVAILABLE"):
                continue

            if self.is_room_hidden(r["unit"], r["building"]):
                continue

            has_p = r.get("has_photos", "")
            if "Chưa có" in has_p or "(0)" in has_p:
                continue

            # Kiểm tra xem có thư mục ảnh thực tế không
            photo_dir = r.get("photo_dir") or resolve_room_image_dir(r["unit"], r["building"], self.ent_folder.get().strip())
            if not photo_dir or not Path(photo_dir).exists():
                continue

            valid_photos = [f for f in Path(photo_dir).iterdir() if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
            if not valid_photos:
                continue

            candidates.append(r)
        return candidates

    def get_auto_group_pool(self):
        pool = []
        seen = set()

        # 1. Nhóm từ ô danh sách hiện tại
        raw_text = self.txt_groups.get("1.0", "end").strip()
        for line in raw_text.splitlines():
            l_clean = line.split("#")[0].strip()
            if l_clean.startswith("http"):
                norm = normalize_group_base_url(l_clean)
                if norm and norm not in seen:
                    pool.append(norm)
                    seen.add(norm)

        # 2. Bổ sung từ Kho nhóm sạch (Ưu tiên INSTANT -> PENDING)
        instant_list = []
        pending_list = []
        other_clean = []
        for g in self.clean_groups:
            u = g.get("url", "")
            t = g.get("type", "INSTANT")
            if t == "INSTANT":
                instant_list.append(u)
            elif t == "PENDING":
                pending_list.append(u)
            else:
                other_clean.append(u)

        for g_url in instant_list + other_clean + pending_list + self.joined_groups:
            norm = normalize_group_base_url(g_url)
            if norm and norm not in seen:
                pool.append(norm)
                seen.add(norm)

        return pool

    def trigger_auto_post_10(self):
        if self.is_posting:
            messagebox.showwarning("Đang xử lý", "Hệ thống đang chạy một tác vụ. Vui lòng chờ tác vụ hiện tại hoàn tất.")
            return

        candidate_rooms = self.get_candidate_rooms_for_auto()
        if not candidate_rooms:
            messagebox.showwarning(
                "Không có căn phù hợp",
                "Không tìm thấy căn nào thỏa mãn đồng thời:\n"
                "1. Trạng thái: NOW hoặc AVAILABLE\n"
                "2. Đã có kho ảnh hợp lệ\n"
                "3. Không bị ẩn (Không nằm trong danh sách ẩn)\n\n"
                "Vui lòng kiểm tra lại bảng danh sách hoặc bấm 'Bỏ ẩn tất cả' nếu cần."
            )
            return

        group_pool = self.get_auto_group_pool()
        if not group_pool:
            messagebox.showwarning(
                "Chưa có nhóm",
                "Không tìm thấy link nhóm nào hợp lệ trong ô đăng bài hoặc Kho Nhóm Sạch.\n"
                "Vui lòng nhập thêm link nhóm hoặc bấm '📥 Lấy nhóm từ Sheet Báo Cáo' / '📥 Tải Kho Nhóm từ Drive'."
            )
            return

        total_cand = len(candidate_rooms)
        total_grp = len(group_pool)
        cf = messagebox.askyesno(
            "Xác nhận Tự động đăng đủ 10 bài",
            f"🎯 Phát hiện {total_cand} căn đủ điều kiện (NOW/AVAILABLE, có ảnh, không bị ẩn).\n"
            f"📋 Đã chuẩn bị sẵn {total_grp} nhóm để duyệt đăng bài.\n\n"
            f"🛡️ Thuật toán bảo vệ nick FB:\n"
            f" • Xoay vòng luân phiên các căn đủ điều kiện giữa các nhóm (tránh trùng ảnh/text).\n"
            f" • Spin nội dung ngẫu nhiên cho từng bài.\n"
            f" • Nghỉ giãn cách ngẫu nhiên 60s - 110s giữa các bài đăng.\n"
            f" • Tự động dừng và báo cáo lên Google Sheet ngay khi ĐỦ 10 LINK BÀI.\n\n"
            f"Bạn có muốn bắt đầu ngay?"
        )
        if not cf:
            return

        threading.Thread(target=self.execute_auto_post_10, args=(candidate_rooms, group_pool), daemon=True).start()

    def trigger_stop_auto_post(self):
        if not self.is_posting:
            return
        self.stop_requested = True
        self.log("🛑 ĐÃ YÊU CẦU DỪNG ĐĂNG BÀI! Hệ thống sẽ dừng an toàn ngay sau khi hoàn tất thao tác dở dang...")
        if hasattr(self, "btn_stop_auto"):
            self.btn_stop_auto.config(state="disabled")
        if hasattr(self, "status_bar"):
            self.status_bar.config(text="🛑 Đang dừng tiến trình theo yêu cầu của bạn...")

    def execute_auto_post_10(self, candidate_rooms, group_pool):
        self.is_posting = True
        self.stop_requested = False
        self.set_action_buttons_state("disabled")
        if hasattr(self, "btn_stop_auto"):
            self.btn_stop_auto.config(state="normal")

        TARGET_POSTED_COUNT = 10
        posted_records = []
        room_cycle_idx = 0
        group_idx = 0
        template_mode = self.cmb_template.get()
        auto_rejoin = self.chk_auto_rejoin.get()
        auto_submit = self.chk_auto_click_post.get()

        self.log("=" * 65)
        self.log(f"🎯 BẮT ĐẦU CHẾ ĐỘ TỰ ĐỘNG ĐĂNG ĐỦ 10 BÀI & BÁO CÁO")
        self.log(f"📋 Căn đủ điều kiện: {len(candidate_rooms)} căn | Nhóm dự kiến: {len(group_pool)} nhóm | Mẫu: {template_mode}")
        self.log("=" * 65)

        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=FB_CHROME_PROFILE_DIR,
                    channel="chrome",
                    headless=False,
                    viewport={"width": 1280, "height": 850},
                    ignore_default_args=["--enable-automation"],
                    args=["--disable-blink-features=AutomationControlled", "--disable-notifications"]
                )
                context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
                page = context.pages[0] if context.pages else context.new_page()

                while group_idx < len(group_pool) and len(posted_records) < TARGET_POSTED_COUNT:
                    if self.stop_requested:
                        self.log("🛑 Người dùng đã yêu cầu dừng tiến trình tự động.")
                        break

                    group_url = group_pool[group_idx]
                    group_idx += 1

                    current_room = candidate_rooms[room_cycle_idx % len(candidate_rooms)]
                    room_cycle_idx += 1

                    short_bld = format_report_building_short(current_room.get("building", ""))
                    area_tag = f" ({current_room['area']})" if current_room.get("area") else ""
                    post_label = f"{current_room.get('unit', '').strip()} - {short_bld}{area_tag}".strip(" -")
                    today_str = datetime.now().strftime("%d-%m-%Y").lstrip("0").replace("-0", "-")

                    current_success = len(posted_records)
                    self.log(f"➡️ [Tiến độ: {current_success}/{TARGET_POSTED_COUNT} bài] Duyệt nhóm [{group_idx}/{len(group_pool)}]: {group_url} | Chọn {post_label}")
                    if hasattr(self, "lbl_auto_progress"):
                        self.lbl_auto_progress.config(
                            text=f"🎯 Tiến độ: {current_success}/{TARGET_POSTED_COUNT} bài | Đang duyệt nhóm {group_idx}/{len(group_pool)}"
                        )

                    try:
                        page.goto(group_url, wait_until="domcontentloaded", timeout=45000)
                        time.sleep(random.uniform(3.5, 5.0))

                        if "login" in page.url or page.locator("input[name='email']").count() > 0:
                            self.log("🔐 Chưa đăng nhập Facebook! Vui lòng đăng nhập trên Chrome (chờ tối đa 120s)...")
                            fb_ok = False
                            for _ in range(120):
                                if self.stop_requested:
                                    break
                                if "login" not in page.url and page.locator("input[name='email']").count() == 0:
                                    fb_ok = True
                                    self.log("✅ Đã nhận diện đăng nhập Facebook thành công!")
                                    time.sleep(2.0)
                                    break
                                time.sleep(1.0)
                            if self.stop_requested:
                                break
                            if not fb_ok:
                                self.log("⚠️ Hết thời gian chờ đăng nhập Facebook. Bỏ qua nhóm này.")
                                continue
                            if "/groups/" not in page.url:
                                page.goto(group_url, wait_until="domcontentloaded", timeout=45000)
                                time.sleep(3.0)

                        # Kiểm tra bị chặn
                        blocked_banner = page.locator("text=/nội dung này hiện không hiển thị|content isn't available|bị chặn|suspended/i").first
                        if blocked_banner.count() > 0:
                            self.log(f"🚫 Nhóm {group_url} không khả dụng hoặc chặn tài khoản -> Bỏ qua.")
                            self.remove_from_clean_groups(group_url)
                            continue

                        # Kiểm tra bị kích
                        kicked_join_btn = page.locator(
                            "div[role='button']:has-text('Tham gia nhóm'), "
                            "div[role='button']:has-text('Join group'), "
                            "div[role='button']:has-text('Join Group'), "
                            "[aria-label*='Tham gia nhóm'], "
                            "[aria-label*='Join group']"
                        ).first

                        if kicked_join_btn.count() > 0 and kicked_join_btn.is_visible():
                            self.log(f"⚠️ Nhóm {group_url}: Tài khoản chưa vào nhóm hoặc đã bị kích.")
                            self.remove_from_clean_groups(group_url)
                            if auto_rejoin:
                                try:
                                    kicked_join_btn.click()
                                    time.sleep(2.0)
                                    q_dlg = page.locator("div[role='dialog']:has-text('Trả lời câu hỏi'), div[role='dialog']:has-text('Answer questions')").first
                                    if q_dlg.count() > 0:
                                        close_b = page.locator("div[role='dialog'] [aria-label='Đóng'], div[role='dialog'] [aria-label='Close']").first
                                        if close_b.count() > 0:
                                            close_b.click()
                                    else:
                                        self.log("🔄 Đã tự động gửi yêu cầu xin vào lại nhóm.")
                                except Exception:
                                    pass
                            continue

                        # Tab Thảo luận
                        discussion_tab = page.locator("a[role='tab']:has-text('Thảo luận'), a[role='tab']:has-text('Discussion')").first
                        if discussion_tab.count() > 0:
                            try:
                                discussion_tab.click(timeout=3000)
                                time.sleep(2)
                            except Exception:
                                pass

                        # Tìm ô đăng bài
                        composer_btn = page.locator(
                            "div[role='button']:has-text('Bạn viết gì đi'), "
                            "div[role='button']:has-text('Write something'), "
                            "div[role='button']:has-text('Tạo bài viết'), "
                            "div[role='button']:has-text('Create a public post'), "
                            "div[role='button']:has-text('Create a post'), "
                            "div[role='button']:has-text('Bạn đang nghĩ gì'), "
                            "[aria-label*='Tạo bài viết'], "
                            "[aria-label*='Write something']"
                        ).first

                        if composer_btn.count() == 0:
                            self.log(f"⏳ Nhóm {group_url} chưa mở khung đăng bài (chờ duyệt hoặc tắt đăng). Bỏ qua.")
                            continue

                        page.mouse.wheel(0, random.randint(200, 380))
                        time.sleep(1.2)

                        composer_btn.wait_for(state="visible", timeout=15000)
                        composer_btn.click()
                        time.sleep(random.uniform(2.0, 3.0))

                        # Spin nội dung riêng cho căn này
                        final_text = build_post_message(current_room, template_mode=template_mode, spin=True)

                        textbox = page.locator("div[role='dialog'] div[role='textbox']").first
                        textbox.wait_for(state="visible", timeout=10000)
                        textbox.click()
                        time.sleep(0.5)
                        pyperclip.copy(final_text)
                        page.keyboard.press("Control+V")
                        time.sleep(1.5)

                        # Nạp ảnh của căn
                        photo_source = current_room.get("photo_dir") or self.ent_folder.get().strip()
                        image_paths = self.prepare_room_photos(current_room["unit"], photo_source, building=current_room.get("building"))
                        if image_paths:
                            self.log(f"📸 Đang tải {len(image_paths)} ảnh của Căn {current_room['unit']}...")
                            file_input = page.locator("div[role='dialog'] input[type='file']").first
                            if file_input.count() == 0:
                                photo_btn = page.locator(
                                    "div[role='dialog'] [aria-label*='Ảnh/video'], "
                                    "div[role='dialog'] [aria-label*='Photo/video'], "
                                    "div[role='dialog'] [aria-label*='Ảnh'], "
                                    "div[role='dialog'] [aria-label*='Photo'], "
                                    "div[role='dialog'] div[role='button']:has-text('Ảnh'), "
                                    "div[role='dialog'] div[role='button']:has-text('Photo')"
                                ).first
                                if photo_btn.count() > 0:
                                    photo_btn.click()
                                    time.sleep(1.2)
                                file_input = page.locator("div[role='dialog'] input[type='file']").first

                            if file_input.count() > 0:
                                file_input.set_input_files(image_paths)
                                wait_upload = max(5.0, len(image_paths) * 1.5)
                                time.sleep(wait_upload)

                        # Bấm Đăng
                        if auto_submit:
                            post_btn = page.locator(
                                "div[role='dialog'] div[aria-label='Đăng'], "
                                "div[role='dialog'] div[aria-label='Post'], "
                                "div[role='dialog'] div[role='button']:has-text('Đăng'), "
                                "div[role='dialog'] div[role='button']:has-text('Post')"
                            ).last
                            post_btn.wait_for(state="visible", timeout=12000)
                            for _ in range(30):
                                if post_btn.get_attribute("aria-disabled") != "true":
                                    break
                                time.sleep(1.0)
                            post_btn.click()
                            self.log(f"✅ Đã bấm ĐĂNG tại nhóm: {group_url}")

                            try:
                                page.locator("div[role='dialog']").wait_for(state="hidden", timeout=25000)
                            except Exception:
                                pass
                            time.sleep(4.0)
                        else:
                            self.log(f"📝 Đã điền sẵn bài & ảnh tại nhóm [{group_idx}]. Mời bạn kiểm tra và bấm Đăng trên Chrome (chờ 25s)...")
                            time.sleep(25)

                        # Trích xuất link và trạng thái
                        g_name, p_url, p_status = self.extract_group_name_and_post_url(page, group_url, unit_id=current_room.get("unit", ""))

                        if p_status in ("Đã đăng", "Đang chờ phê duyệt"):
                            posted_records.append({
                                "group_name": g_name,
                                "post_label": post_label,
                                "post_url": p_url,
                                "date_str": today_str,
                                "status": p_status,
                            })

                            if p_status == "Đã đăng":
                                self.add_or_update_group(group_url, group_name=g_name, group_type="INSTANT", last_status="Đã đăng", member_status="Đã là thành viên", note="Tự động đăng thành công")
                            else:
                                self.add_or_update_group(group_url, group_name=g_name, group_type="PENDING", last_status="Đang chờ phê duyệt", member_status="Đã là thành viên", note="Bài vào mục Chờ duyệt")

                            self.log(f"🎉 [TIẾN ĐỘ THÀNH CÔNG: {len(posted_records)}/{TARGET_POSTED_COUNT} BÀI] {g_name} | {post_label} | {p_status} -> {p_url}")

                            if hasattr(self, "lbl_auto_progress"):
                                self.lbl_auto_progress.config(
                                    text=f"🎯 Tiến độ: Đã xong {len(posted_records)}/{TARGET_POSTED_COUNT} bài!"
                                )

                        # Nghỉ an toàn nếu chưa đạt đủ mục tiêu 10 bài và chưa bị dừng
                        if len(posted_records) < TARGET_POSTED_COUNT and not self.stop_requested and group_idx < len(group_pool):
                            delay = random.randint(60, 110)
                            self.log(f"🛡️ [BẢO VỆ TÀI KHOẢN FB] Nghỉ an toàn {delay} giây trước khi duyệt bài tiếp theo...")
                            for s in range(delay, 0, -1):
                                if self.stop_requested:
                                    break
                                if s % 10 == 0 or s <= 5:
                                    if hasattr(self, "status_bar"):
                                        self.status_bar.config(
                                            text=f"🛡️ Nghỉ an toàn chống checkpoint: còn {s} giây (Tiến độ: {len(posted_records)}/{TARGET_POSTED_COUNT} bài)..."
                                        )
                                time.sleep(1.0)

                    except Exception as e:
                        self.log(f"❌ Lỗi xử lý tại nhóm {group_url}: {e}")
                        continue

                # Hoàn tất vòng lặp: Tự động ghi Sheet Báo Cáo
                if posted_records:
                    self.log(f"📊 Đang tự động ghi {len(posted_records)} bài vừa đăng lên Google Sheet Báo Cáo...")
                    self.write_reports_to_google_sheet(context, posted_records)
                    self.sync_groups_to_google_sheet(context=context, silent=True)
                    self.log(f"✅ ĐÃ TỰ ĐỘNG BÁO CÁO THÀNH CÔNG {len(posted_records)} LINK BÀI LÊN DÒNG 5 CỦA SHEET BÁO CÁO!")

                try:
                    context.close()
                except Exception:
                    pass

            if len(posted_records) >= TARGET_POSTED_COUNT:
                self.log("=" * 65)
                self.log(f"🏆 XUẤT SẮC! ĐÃ HOÀN THÀNH MỤC TIÊU ĐĂNG ĐỦ {TARGET_POSTED_COUNT} LINK BÀI & TỰ BÁO CÁO XONG!")
                self.log("=" * 65)
                if hasattr(self, "lbl_auto_progress"):
                    self.lbl_auto_progress.config(
                        text=f"🏆 ĐÃ HOÀN THÀNH ĐỦ {TARGET_POSTED_COUNT}/{TARGET_POSTED_COUNT} BÀI BÁO CÁO!"
                    )
                messagebox.showinfo(
                    "Hoàn thành xuất sắc",
                    f"🎉 Hệ thống đã đăng và tự động báo cáo thành công ĐỦ {TARGET_POSTED_COUNT} LINK BÀI VIẾT!\n\n"
                    f"Toàn bộ {TARGET_POSTED_COUNT} link bài đã được dán lên đầu Sheet Báo Cáo (Dòng 5 thẻ Trang tính1) và đồng bộ Kho Nhóm sạch."
                )
            else:
                self.log(f"ℹ️ Phiên tự động kết thúc. Đã ghi nhận và báo cáo {len(posted_records)}/{TARGET_POSTED_COUNT} bài viết.")
                if hasattr(self, "lbl_auto_progress"):
                    self.lbl_auto_progress.config(
                        text=f"ℹ️ Đã dừng: Ghi nhận {len(posted_records)}/{TARGET_POSTED_COUNT} bài."
                    )
                messagebox.showinfo(
                    "Đã hoàn thành phiên",
                    f"Phiên làm việc kết thúc.\n"
                    f"Đã đăng và tự động báo cáo {len(posted_records)} link bài viết lên Google Sheet."
                )
        except Exception as e:
            self.log(f"❌ Lỗi nghiêm trọng trong phiên tự động: {e}")
        finally:
            self.is_posting = False
            self.stop_requested = False
            self.set_action_buttons_state("normal")
            if hasattr(self, "btn_stop_auto"):
                self.btn_stop_auto.config(state="disabled")
            if hasattr(self, "status_bar"):
                self.status_bar.config(text="🟢 Hệ thống sẵn sàng.")

    # ----------------- ĐĂNG CĂN ĐÃ CHỌN -----------------
    def trigger_post_selected(self):
        if self.is_posting:
            messagebox.showwarning("Đang xử lý", "Hệ thống đang chạy một phiên tác vụ FB. Vui lòng chờ.")
            return

        room = self.get_selected_room()
        if not room:
            messagebox.showinfo("Chưa chọn", "Vui lòng bấm chọn một căn trong danh sách trước khi đăng.")
            return

        preview_text = self.txt_message.get("1.0", "end").strip()

        def worker():
            self.is_posting = True
            self.set_action_buttons_state("disabled")
            try:
                photo_source = room.get("photo_dir") or self.ent_folder.get().strip()
                photos = self.prepare_room_photos(room["unit"], photo_source, building=room.get("building"))
                self.execute_post_to_fb_groups(preview_text, photos, room)
                self.log(f"🎉 XONG PHIÊN ĐĂNG FB & BÁO CÁO: Căn {room['unit']} - {room['building']}")
            except Exception as e:
                self.log(f"❌ Lỗi đăng bài FB: {e}")
            finally:
                self.is_posting = False
                self.set_action_buttons_state("normal")

        threading.Thread(target=worker, daemon=True).start()

    # ----------------- HẸN GIỜ TỰ ĐỘNG -----------------
    def toggle_schedule(self):
        self.auto_schedule_enabled = bool(self.chk_auto_var.get())
        if self.auto_schedule_enabled:
            self.log(f"⏰ ĐÃ KÍCH HOẠT HẸN GIỜ FB: {', '.join(SCHEDULE_SLOTS)}.")
        else:
            self.log("Đã tắt chế độ hẹn giờ tự động.")

    def start_clock_thread(self):
        def clock():
            while True:
                now = datetime.now()
                c_time = now.strftime("%H:%M")
                c_date = now.strftime("%Y-%m-%d")

                if c_date != self.today_date:
                    self.today_date = c_date
                    self.scheduled_posted_today.clear()

                if self.auto_schedule_enabled and not self.is_posting:
                    for slot in SCHEDULE_SLOTS:
                        if c_time == slot and slot not in self.scheduled_posted_today:
                            self.scheduled_posted_today.add(slot)
                            self.log(f"🔔 ĐẾN KHUNG GIỜ HẸN {slot}: Tự động đăng căn đang chọn lên FB...")
                            self.trigger_post_selected()
                            break

                time.sleep(25)
        threading.Thread(target=clock, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = FBGroupPosterApp(root)
    root.mainloop()
