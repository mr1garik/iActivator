"""Marketing names for iPhone model identifiers (ProductType)."""
from __future__ import annotations

from typing import Optional

from .i18n import t

IPHONES = {
    "iPhone3,1": "iPhone 4", "iPhone3,2": "iPhone 4", "iPhone3,3": "iPhone 4",
    "iPhone4,1": "iPhone 4S",
    "iPhone5,1": "iPhone 5", "iPhone5,2": "iPhone 5",
    "iPhone5,3": "iPhone 5c", "iPhone5,4": "iPhone 5c",
    "iPhone6,1": "iPhone 5s", "iPhone6,2": "iPhone 5s",
    "iPhone7,2": "iPhone 6", "iPhone7,1": "iPhone 6 Plus",
    "iPhone8,1": "iPhone 6s", "iPhone8,2": "iPhone 6s Plus", "iPhone8,4": "iPhone SE (1-го поколения)",
    "iPhone9,1": "iPhone 7", "iPhone9,3": "iPhone 7", "iPhone9,2": "iPhone 7 Plus", "iPhone9,4": "iPhone 7 Plus",
    "iPhone10,1": "iPhone 8", "iPhone10,4": "iPhone 8", "iPhone10,2": "iPhone 8 Plus", "iPhone10,5": "iPhone 8 Plus",
    "iPhone10,3": "iPhone X", "iPhone10,6": "iPhone X",
    "iPhone11,2": "iPhone XS", "iPhone11,4": "iPhone XS Max", "iPhone11,6": "iPhone XS Max", "iPhone11,8": "iPhone XR",
    "iPhone12,1": "iPhone 11", "iPhone12,3": "iPhone 11 Pro", "iPhone12,5": "iPhone 11 Pro Max",
    "iPhone12,8": "iPhone SE (2-го поколения)",
    "iPhone13,1": "iPhone 12 mini", "iPhone13,2": "iPhone 12", "iPhone13,3": "iPhone 12 Pro", "iPhone13,4": "iPhone 12 Pro Max",
    "iPhone14,4": "iPhone 13 mini", "iPhone14,5": "iPhone 13", "iPhone14,2": "iPhone 13 Pro", "iPhone14,3": "iPhone 13 Pro Max",
    "iPhone14,6": "iPhone SE (3-го поколения)",
    "iPhone14,7": "iPhone 14", "iPhone14,8": "iPhone 14 Plus", "iPhone15,2": "iPhone 14 Pro", "iPhone15,3": "iPhone 14 Pro Max",
    "iPhone15,4": "iPhone 15", "iPhone15,5": "iPhone 15 Plus", "iPhone16,1": "iPhone 15 Pro", "iPhone16,2": "iPhone 15 Pro Max",
    "iPhone17,3": "iPhone 16", "iPhone17,4": "iPhone 16 Plus", "iPhone17,1": "iPhone 16 Pro", "iPhone17,2": "iPhone 16 Pro Max",
    "iPhone17,5": "iPhone 16e",
    "iPhone18,3": "iPhone 17", "iPhone18,4": "iPhone Air", "iPhone18,1": "iPhone 17 Pro", "iPhone18,2": "iPhone 17 Pro Max",
    "iPhone18,5": "iPhone 17e",
    # 2026: identifiers as listed by EveryMac/AppleDB; the other iPhone19,x stay as identifiers until confirmed.
    "iPhone19,2": "iPhone 18 Pro", "iPhone19,3": "iPhone 18 Pro Max", "iPhone19,7": "iPhone 18 Pro Max",
}

# iPads: the year (or number) Apple uses for the generation, so the name needs no translation.
IPADS = {}
for _ids, _name in (
    ("2,1 2,2 2,3 2,4", "iPad 2"), ("3,1 3,2 3,3", "iPad 3"), ("3,4 3,5 3,6", "iPad 4"),
    ("6,11 6,12", "iPad (2017)"), ("7,5 7,6", "iPad (2018)"), ("7,11 7,12", "iPad (2019)"),
    ("11,6 11,7", "iPad (2020)"), ("12,1 12,2", "iPad (2021)"), ("13,18 13,19", "iPad (2022)"),
    ("15,7 15,8", "iPad (A16)"),
    ("2,5 2,6 2,7", "iPad mini"), ("4,4 4,5 4,6", "iPad mini 2"), ("4,7 4,8 4,9", "iPad mini 3"),
    ("5,1 5,2", "iPad mini 4"), ("11,1 11,2", "iPad mini (2019)"), ("14,1 14,2", "iPad mini (2021)"),
    ("16,1 16,2", "iPad mini (A17 Pro)"),
    ("4,1 4,2 4,3", "iPad Air"), ("5,3 5,4", "iPad Air 2"), ("11,3 11,4", "iPad Air (2019)"),
    ("13,1 13,2", "iPad Air (2020)"), ("13,16 13,17", "iPad Air (2022)"),
    ("14,8 14,9", "iPad Air 11″ (M2)"), ("14,10 14,11", "iPad Air 13″ (M2)"),
    ("15,3 15,4", "iPad Air 11″ (M3)"), ("15,5 15,6", "iPad Air 13″ (M3)"),
    ("6,3 6,4", "iPad Pro 9.7″"), ("6,7 6,8", "iPad Pro 12.9″ (2015)"),
    ("7,1 7,2", "iPad Pro 12.9″ (2017)"), ("7,3 7,4", "iPad Pro 10.5″"),
    ("8,1 8,2 8,3 8,4", "iPad Pro 11″ (2018)"), ("8,5 8,6 8,7 8,8", "iPad Pro 12.9″ (2018)"),
    ("8,9 8,10", "iPad Pro 11″ (2020)"), ("8,11 8,12", "iPad Pro 12.9″ (2020)"),
    ("13,4 13,5 13,6 13,7", "iPad Pro 11″ (2021)"), ("13,8 13,9 13,10 13,11", "iPad Pro 12.9″ (2021)"),
    ("14,3 14,4", "iPad Pro 11″ (2022)"), ("14,5 14,6", "iPad Pro 12.9″ (2022)"),
    ("16,3 16,4", "iPad Pro 11″ (M4)"), ("16,5 16,6", "iPad Pro 13″ (M4)"),
):
    for _id in _ids.split():
        IPADS["iPad" + _id] = _name

_SIZES_GB = [16, 32, 64, 128, 256, 512, 1024, 2048]


def model_name(product_type: Optional[str]) -> str:
    """Unknown (newer) models keep their identifier, e.g. "iPhone19,1"."""
    return IPHONES.get(product_type or "") or IPADS.get(product_type or "", product_type or "iPhone")


def capacity_label(total_bytes: Optional[int]) -> Optional[str]:
    """Round the reported disk size up to the advertised one (a 256 GB iPhone reports ~255.9e9 bytes)."""
    if not total_bytes:
        return None
    gb = total_bytes / 1e9
    size = next((s for s in _SIZES_GB if gb <= s * 1.02), round(gb))
    return t("{n} ТБ", n=size // 1024) if size >= 1024 else t("{n} ГБ", n=size)
