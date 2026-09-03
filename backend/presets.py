"""Arayüzde sunulan konuşma biçimleri ve model ayarları."""

from __future__ import annotations

from typing import TypedDict


class Preset(TypedDict):
    label: str
    description: str
    exaggeration: float
    cfg_weight: float
    temperature: float


PRESETS: dict[str, Preset] = {
    "normal": {
        "label": "Doğal",
        "description": "Günlük kullanım için dengeli ve doğal anlatım.",
        "exaggeration": 0.50,
        "cfg_weight": 0.50,
        "temperature": 0.80,
    },
    "news": {
        "label": "Haber",
        "description": "Daha ölçülü ve net haber sunumu.",
        "exaggeration": 0.35,
        "cfg_weight": 0.62,
        "temperature": 0.70,
    },
    "announcement": {
        "label": "Duyuru",
        "description": "Anons ve kurumsal bilgilendirmeler için belirgin ton.",
        "exaggeration": 0.48,
        "cfg_weight": 0.68,
        "temperature": 0.74,
    },
    "story": {
        "label": "Hikâye",
        "description": "Daha canlı ve duygulu hikâye anlatımı.",
        "exaggeration": 0.72,
        "cfg_weight": 0.45,
        "temperature": 0.92,
    },
    "education": {
        "label": "Eğitim",
        "description": "Ders ve açıklamalar için sakin, anlaşılır anlatım.",
        "exaggeration": 0.38,
        "cfg_weight": 0.66,
        "temperature": 0.72,
    },
    "accessibility": {
        "label": "Erişilebilir",
        "description": "Ekran okuma için düşük duygu ve yüksek anlaşılırlık.",
        "exaggeration": 0.25,
        "cfg_weight": 0.72,
        "temperature": 0.66,
    },
}


TEMPLATES = [
    {
        "id": "ulasim-duyurusu",
        "title": "Ulaşım duyurusu",
        "category": "Duyuru",
        "preset": "announcement",
        "text": "Değerli yolcularımız, aracımız kısa süre içinde hareket edecektir. Lütfen güvenliğiniz için emniyet kemerlerinizi bağlayınız.",
    },
    {
        "id": "haber-girisi",
        "title": "Haber girişi",
        "category": "Haber",
        "preset": "news",
        "text": "İyi akşamlar. Günün öne çıkan gelişmeleriyle ana haber bülteni başlıyor.",
    },
    {
        "id": "egitim-aciklamasi",
        "title": "Eğitim anlatımı",
        "category": "Eğitim",
        "preset": "education",
        "text": "Bu bölümde metinden sese dönüştürme sistemlerinin temel çalışma adımlarını inceleyeceğiz.",
    },
    {
        "id": "hikaye-baslangici",
        "title": "Hikâye başlangıcı",
        "category": "Hikâye",
        "preset": "story",
        "text": "Güneş dağların arkasında kaybolurken küçük kasabanın sokaklarını tatlı bir sessizlik kapladı.",
    },
    {
        "id": "erisilebilirlik",
        "title": "Erişilebilir içerik",
        "category": "Erişilebilirlik",
        "preset": "accessibility",
        "text": "Sayfanın ana bölümünde metin giriş alanı, konuşma biçimi seçenekleri ve ses oluşturma düğmesi bulunmaktadır.",
    },
]

