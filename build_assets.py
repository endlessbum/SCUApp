# -*- coding: utf-8 -*-
"""Сборка ассетов сайта: скрины, карточки и hero-коллаж."""
import os
import shutil
from PIL import Image, ImageFilter

ROOT = r'E:\Серый\Проекты\SCU\Сайт'
ROUND = os.path.join(ROOT, 'Скрины', 'Срины приложения с сглаженными углами')
STRAIGHT = os.path.join(ROOT, 'Скрины', 'Срины приложения с углами 90 градусов')
SCU = os.path.join(ROOT, 'static', 'scuapp')


def fix_name(n):
    """В папке со скруглёнными скринами имена файлов сохранились в mojibake (utf-8 как cp866)."""
    try:
        return n.encode('cp866').decode('utf-8')
    except Exception:
        return n


round_files = {fix_name(f): os.path.join(ROUND, f)
               for f in os.listdir(ROUND) if f.lower().endswith('.png')}
straight_files = {f: os.path.join(STRAIGHT, f)
                  for f in os.listdir(STRAIGHT) if f.lower().endswith('.png')}

print('rounded keys:', sorted(round_files))

# --- 1. Скрины для карусели (прямые углы), имена прежние ---
for src_name, dst_name in [
    ('Установка компонентов.png', 'screen-install.png'),
    ('Удаление мусорного ПО.png', 'screen-cleanup.png'),
    ('Питание, память, CPU.png', 'screen-power.png'),
]:
    shutil.copyfile(straight_files[src_name], os.path.join(SCU, dst_name))

# --- 2. Карточки ---
# Диалог с рабочего стола — вместо старой карточки-уведомления
shutil.copyfile(r'C:\Users\benq\Desktop\Окно UAC.png', os.path.join(SCU, 'card-notification.png'))

# Кроп панели настроек (пропорции подобраны под равную высоту с диалогом в вёрстке)
settings = Image.open(straight_files['Настройки.png'])
card = settings.crop((1440, 200, 1858, 455))
card.save(os.path.join(SCU, 'card-settings.png'))

# --- 3. Hero-коллаж из скруглённых скринов ---
CANVAS_W, CANVAS_H = 2936, 1443
canvas = Image.new('RGBA', (CANVAS_W, CANVAS_H), (255, 255, 255, 255))


def paste_with_shadow(img, pos):
    shadow = Image.new('RGBA', img.size, (0, 0, 0, 80))
    shadow.putalpha(img.split()[3].point(lambda a: 80 if a else 0))
    shadow = shadow.filter(ImageFilter.GaussianBlur(26))
    canvas.alpha_composite(shadow, (pos[0], pos[1] + 16))
    canvas.alpha_composite(img, pos)


def scaled(name, width):
    im = Image.open(round_files[name]).convert('RGBA')
    h = round(im.height * width / im.width)
    return im.resize((width, h), Image.LANCZOS)


# порядок от заднего к переднему
paste_with_shadow(scaled('Главная.png', 1700), (618, 90))
paste_with_shadow(scaled('Установка компонентов.png', 1100), (-140, 680))
paste_with_shadow(scaled('Настройки.png', 1100), (CANVAS_W - 1100 + 140, 680))
paste_with_shadow(scaled('Бэнчмарк.png', 1200), (868, 950))

canvas.convert('RGB').save(os.path.join(ROOT, 'static', 'compositor', 'hero.png'))
print('done')
