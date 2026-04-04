#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
食物识别与热量查询脚本
支持：
  1. 图片识别（Google Vision API 或 MiniMax）
  2. 菜单/外卖截图 OCR（EasyOCR）
  3. 文字描述直接查询（USDA）

用法：
    python3 food_recognition.py --image meal.jpg --meal-type lunch
    python3 food_recognition.py --text "米饭250g 红烧肉150g" --meal-type lunch
    python3 food_recognition.py --image menu.jpg --ocr-mode easyocr --meal-type dinner
"""

import argparse
import base64
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.expanduser("~/.openclaw/.env"))
except ImportError:
    pass

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# 中英文食物名称映射表
FOOD_NAME_MAP = {
    # 主食
    '米饭': 'rice white cooked',
    '白米饭': 'rice white cooked',
    '糙米饭': 'rice brown cooked',
    '面条': 'noodles cooked',
    '乌冬面': 'udon noodles',
    '拉面': 'ramen noodles',
    '包子': 'steamed bun pork',
    '馒头': 'steamed bun plain',
    '饺子': 'dumpling pork',
    '饺子（蒸）': 'dumpling steamed',
    '煎饺': 'pot sticker',
    '炒饭': 'fried rice',
    '寿司': 'sushi',
    '粥': 'rice porridge',
    '燕麦': 'oatmeal cooked',
    '全麦面包': 'bread whole wheat',
    '白面包': 'bread white',
    '土豆': 'potato boiled',
    '红薯': 'sweet potato baked',
    '玉米': 'corn yellow cooked',

    # 肉类
    '鸡胸肉': 'chicken breast cooked',
    '鸡腿': 'chicken leg cooked',
    '牛肉': 'beef ground cooked',
    '猪肉': 'pork cooked',
    '红烧肉': 'pork braised',
    '猪排': 'pork chop cooked',
    '火腿': 'ham cooked',
    '培根': 'bacon cooked',
    '羊肉': 'lamb cooked',
    '鸭肉': 'duck cooked',

    # 海鲜
    '三文鱼': 'salmon cooked',
    '金枪鱼': 'tuna cooked',
    '虾': 'shrimp cooked',
    '螃蟹': 'crab cooked',
    '鱼': 'fish cooked',
    '鲈鱼': 'bass sea cooked',
    '带鱼': 'hairtail fish',
    '鱿鱼': 'squid cooked',

    # 蛋奶
    '鸡蛋': 'egg whole cooked',
    '炒鸡蛋': 'eggs scrambled',
    '煎蛋': 'egg fried',
    '水煮蛋': 'egg hard boiled',
    '牛奶': 'milk whole',
    '低脂牛奶': 'milk low fat',
    '酸奶': 'yogurt plain',
    '希腊酸奶': 'yogurt greek plain',
    '奶酪': 'cheese cheddar',

    # 豆制品
    '豆腐': 'tofu',
    '北豆腐': 'tofu firm',
    '嫩豆腐': 'tofu soft',
    '豆浆': 'soy milk',
    '毛豆': 'edamame cooked',

    # 蔬菜
    '西兰花': 'broccoli cooked',
    '菠菜': 'spinach cooked',
    '青菜': 'bok choy cooked',
    '生菜': 'lettuce raw',
    '番茄': 'tomato raw',
    '黄瓜': 'cucumber raw',
    '胡萝卜': 'carrot cooked',
    '洋葱': 'onion cooked',
    '大白菜': 'cabbage cooked',
    '蘑菇': 'mushrooms cooked',
    '香菇': 'shiitake mushroom cooked',
    '木耳': 'wood ear mushroom',
    '芹菜': 'celery raw',
    '青椒': 'green pepper cooked',
    '茄子': 'eggplant cooked',
    '豆角': 'green beans cooked',
    '南瓜': 'pumpkin cooked',
    '玉米笋': 'baby corn',
    '芦笋': 'asparagus cooked',

    # 水果
    '苹果': 'apple raw',
    '香蕉': 'banana raw',
    '橙子': 'orange raw',
    '葡萄': 'grapes raw',
    '西瓜': 'watermelon raw',
    '草莓': 'strawberries raw',
    '蓝莓': 'blueberries raw',
    '芒果': 'mango raw',
    '桃子': 'peach raw',
    '梨': 'pear raw',

    # 零食/饮料
    '可乐': 'cola carbonated beverage',
    '橙汁': 'orange juice',
    '咖啡': 'coffee black',
    '拿铁': 'latte coffee',
    '花生': 'peanuts roasted',
    '腰果': 'cashews roasted',
    '核桃': 'walnuts raw',
    '薯片': 'potato chips',
    '饼干': 'crackers',
    '巧克力': 'chocolate dark',
    '冰淇淋': 'ice cream vanilla',
}

# 常见食物热量参考表（当 USDA 查询失败时使用，单位：kcal/100g）
FALLBACK_CALORIES = {
    '米饭': 116,
    '白米饭': 116,
    '面条': 138,
    '包子': 223,
    '馒头': 233,
    '饺子': 240,
    '鸡胸肉': 165,
    '牛肉': 250,
    '猪肉': 297,
    '红烧肉': 380,
    '鸡蛋': 155,
    '豆腐': 76,
    '三文鱼': 208,
    '西兰花': 34,
    '菠菜': 23,
    '番茄': 18,
    '苹果': 52,
    '香蕉': 89,
}


def recognize_with_google_vision(image_path: str) -> list:
    """
    使用 Google Vision API 识别图片中的食物

    Args:
        image_path: 图片路径

    Returns:
        识别到的食物名称列表
    """
    try:
        import requests

        api_key = os.getenv('GOOGLE_VISION_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_VISION_API_KEY 未配置")

        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        payload = {
            "requests": [
                {
                    "image": {"content": image_data},
                    "features": [
                        {"type": "LABEL_DETECTION", "maxResults": 20},
                        {"type": "OBJECT_LOCALIZATION", "maxResults": 10}
                    ]
                }
            ]
        }

        response = requests.post(
            f'https://vision.googleapis.com/v1/images:annotate?key={api_key}',
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        food_items = []
        responses = data.get('responses', [{}])[0]

        # 从标签中提取食物相关标签
        food_categories = {'food', 'dish', 'cuisine', 'ingredient', 'meal', 'recipe'}
        for label in responses.get('labelAnnotations', []):
            desc = label.get('description', '').lower()
            score = label.get('score', 0)
            # 只取置信度较高的食物标签
            if score > 0.7 and any(cat in desc for cat in food_categories):
                food_items.append(label['description'])
            elif score > 0.8:
                food_items.append(label['description'])

        logger.info(f"Google Vision 识别到 {len(food_items)} 个标签")
        return food_items

    except ImportError:
        logger.warning("requests 库未安装")
        return []
    except Exception as e:
        logger.error(f"Google Vision API 调用失败：{e}")
        return []


def recognize_with_minimax(image_path: str) -> list:
    """
    使用 MiniMax M2.7 识别图片中的食物

    Args:
        image_path: 图片路径

    Returns:
        识别到的食物描述列表（格式：["食物名 重量g", ...]）
    """
    try:
        import requests

        api_key = os.getenv('MINIMAX_API_KEY')
        group_id = os.getenv('MINIMAX_GROUP_ID')
        if not api_key or not group_id:
            raise ValueError("MINIMAX_API_KEY 或 MINIMAX_GROUP_ID 未配置")

        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        # 获取图片 MIME 类型
        ext = Path(image_path).suffix.lower()
        mime_map = {'.jpg': 'jpeg', '.jpeg': 'jpeg', '.png': 'png', '.webp': 'webp'}
        mime_type = mime_map.get(ext, 'jpeg')

        payload = {
            "model": "abab6.5s-chat",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/{mime_type};base64,{image_data}"}
                        },
                        {
                            "type": "text",
                            "text": "请识别图片中所有食物，以JSON格式返回列表，每项包含name(中文名)和weight_g(估计克数)。如果无法确定克数，根据常见份量估算。只返回JSON，不要其他文字。格式：[{\"name\":\"食物名\",\"weight_g\":数字}]"
                        }
                    ]
                }
            ],
            "max_tokens": 500
        }

        response = requests.post(
            f'https://api.minimax.chat/v1/text/chatcompletion_v2?GroupId={group_id}',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        logger.debug(f"MiniMax 响应：{content}")

        # 尝试解析 JSON 响应
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            items = json.loads(json_match.group())
            return [f"{item['name']} {item.get('weight_g', 0)}g" for item in items]

        return [content] if content else []

    except Exception as e:
        logger.error(f"MiniMax API 调用失败：{e}")
        return []


def recognize_with_easyocr(image_path: str) -> list:
    """
    使用 EasyOCR 识别菜单或外卖截图中的文字，提取食物名称

    Args:
        image_path: 图片路径

    Returns:
        识别到的文字列表
    """
    try:
        import easyocr

        model_dir = os.path.expanduser('~/.EasyOCR/')
        reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, model_storage_directory=model_dir)
        results = reader.readtext(image_path)

        texts = [text for _, text, conf in results if conf > 0.5]
        logger.info(f"EasyOCR 识别到 {len(texts)} 个文字区域")
        return texts

    except ImportError:
        logger.error("EasyOCR 未安装")
        return []
    except Exception as e:
        logger.error(f"EasyOCR 识别失败：{e}")
        return []


def parse_text_input(text: str) -> list:
    """
    解析文字输入，提取食物名称和重量

    支持格式：
    - "米饭250g 红烧肉150g"
    - "米饭 250g，红烧肉 150g"
    - "一碗米饭，两块红烧肉"

    Args:
        text: 用户输入的文字

    Returns:
        解析出的食物列表 [{"name": "...", "weight_g": ...}, ...]
    """
    items = []

    # 分割多个食物（支持中文逗号、空格、顿号分隔）
    parts = re.split(r'[，,、\s]+', text.strip())

    for part in parts:
        if not part:
            continue

        # 匹配 "食物名 重量g" 格式
        match = re.match(r'(.+?)(\d+\.?\d*)\s*[gG克]', part)
        if match:
            name = match.group(1).strip()
            weight = float(match.group(2))
            items.append({'name': name, 'weight_g': weight})
        else:
            # 没有重量，使用默认份量
            name = re.sub(r'[一两三四五六七八九十百克g份碗盘]', '', part).strip()
            if name:
                # 根据单位词估算重量
                if '碗' in part:
                    weight = 250.0
                elif '盘' in part:
                    weight = 300.0
                elif '份' in part:
                    weight = 200.0
                elif '个' in part:
                    weight = 100.0
                else:
                    weight = 150.0  # 默认
                items.append({'name': name, 'weight_g': weight, 'estimated': True})

    return items


def lookup_usda_calories(food_name: str, weight_g: float) -> dict:
    """
    查询 USDA 数据库获取食物热量

    Args:
        food_name: 食物名称（优先英文，中文会自动转换）
        weight_g: 重量（克）

    Returns:
        营养信息字典
    """
    import sys
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    usda_module = os.path.join(skill_dir, 'usda-lookup', 'usda_lookup.py')

    if os.path.exists(usda_module):
        # 动态加载 usda_lookup 模块
        import importlib.util
        spec = importlib.util.spec_from_file_location("usda_lookup", usda_module)
        usda = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(usda)
        return usda.lookup_food(food_name, weight_g)
    else:
        # 直接调用 USDA API
        return _direct_usda_lookup(food_name, weight_g)


def _direct_usda_lookup(food_name: str, weight_g: float) -> dict:
    """直接调用 USDA API"""
    try:
        import requests

        api_key = os.getenv('USDA_API_KEY', 'DEMO_KEY')

        # 转换中文名为英文
        query = FOOD_NAME_MAP.get(food_name, food_name)

        response = requests.get(
            'https://api.nal.usda.gov/fdc/v1/foods/search',
            params={
                'query': query,
                'api_key': api_key,
                'dataType': ['Foundation', 'SR Legacy'],
                'pageSize': 3
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        foods = data.get('foods', [])
        if not foods:
            return _fallback_calories(food_name, weight_g)

        food = foods[0]
        nutrients = {n['nutrientName']: n['value'] for n in food.get('foodNutrients', [])}

        energy_per_100g = nutrients.get('Energy', 0)
        protein_per_100g = nutrients.get('Protein', 0)
        carbs_per_100g = nutrients.get('Carbohydrate, by difference', 0)
        fat_per_100g = nutrients.get('Total lipid (fat)', 0)

        factor = weight_g / 100.0
        return {
            'food_name': food_name,
            'food_name_en': food.get('description', query),
            'weight_g': weight_g,
            'calories': round(energy_per_100g * factor),
            'protein_g': round(protein_per_100g * factor, 1),
            'carbs_g': round(carbs_per_100g * factor, 1),
            'fat_g': round(fat_per_100g * factor, 1),
            'source': 'USDA'
        }

    except Exception as e:
        logger.warning(f"USDA 查询失败：{e}，使用备用热量表")
        return _fallback_calories(food_name, weight_g)


def _fallback_calories(food_name: str, weight_g: float) -> dict:
    """使用备用热量参考表"""
    # 模糊匹配
    kcal_per_100g = None
    for key, val in FALLBACK_CALORIES.items():
        if key in food_name or food_name in key:
            kcal_per_100g = val
            break

    if kcal_per_100g is None:
        kcal_per_100g = 150  # 默认估算值

    calories = round(kcal_per_100g * weight_g / 100)
    return {
        'food_name': food_name,
        'food_name_en': FOOD_NAME_MAP.get(food_name, food_name),
        'weight_g': weight_g,
        'calories': calories,
        'protein_g': None,
        'carbs_g': None,
        'fat_g': None,
        'source': 'fallback'
    }


def process_food_items(raw_items: list) -> list:
    """
    处理食物列表，查询每种食物的热量

    Args:
        raw_items: 原始食物列表 [{"name": "...", "weight_g": ...}, ...]

    Returns:
        含热量信息的食物列表
    """
    results = []
    for item in raw_items:
        name = item.get('name', '')
        weight = item.get('weight_g', 150)

        if not name:
            continue

        logger.info(f"查询热量：{name} {weight}g")
        nutrition = _direct_usda_lookup(name, weight)
        nutrition['estimated'] = item.get('estimated', False)
        results.append(nutrition)

    return results


def format_user_message(items: list, meal_type: str, total_calories: int) -> str:
    """生成用户友好的回复消息"""
    meal_names = {
        'breakfast': '🍳 早餐',
        'lunch': '🍱 午餐',
        'dinner': '🍜 晚餐',
        'snack': '🍎 零食'
    }
    meal_name = meal_names.get(meal_type, '🍽️ 餐食')

    lines = [f"{meal_name}识别结果："]
    for item in items:
        name = item.get('food_name', '未知')
        weight = item.get('weight_g', 0)
        cals = item.get('calories', 0)
        estimated = '（估算）' if item.get('estimated') else ''
        source = '⚠️' if item.get('source') == 'fallback' else ''
        lines.append(f"• {name} ({weight}g): {cals} kcal {source}{estimated}")

    lines.append(f"📊 合计：{total_calories} kcal")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='食物识别与热量查询工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--image', help='餐食图片路径')
    group.add_argument('--text', help='食物文字描述')
    parser.add_argument('--meal-type', choices=['breakfast', 'lunch', 'dinner', 'snack'],
                        default='lunch', help='餐次类型')
    parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), help='日期 YYYY-MM-DD')
    parser.add_argument('--output', help='输出 JSON 文件路径')
    parser.add_argument('--ocr-mode', choices=['vision', 'minimax', 'easyocr'],
                        default='vision', help='图片识别模式')
    parser.add_argument('--debug', action='store_true', help='启用调试日志')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    raw_items = []

    if args.image:
        image_path = os.path.expanduser(args.image)

        if args.ocr_mode == 'vision':
            logger.info("使用 Google Vision API 识别食物...")
            food_labels = recognize_with_google_vision(image_path)
            if not food_labels:
                logger.warning("Google Vision 失败，尝试 MiniMax...")
                food_descriptions = recognize_with_minimax(image_path)
                # MiniMax 返回格式：["食物名 重量g", ...]
                for desc in food_descriptions:
                    parsed = parse_text_input(desc)
                    raw_items.extend(parsed)
            else:
                # Vision API 返回标签，需要估算重量
                for label in food_labels[:5]:  # 最多取 5 个食物
                    raw_items.append({'name': label, 'weight_g': 150, 'estimated': True})

        elif args.ocr_mode == 'minimax':
            logger.info("使用 MiniMax 识别食物...")
            food_descriptions = recognize_with_minimax(image_path)
            for desc in food_descriptions:
                parsed = parse_text_input(desc)
                raw_items.extend(parsed)

        elif args.ocr_mode == 'easyocr':
            logger.info("使用 EasyOCR 识别菜单/外卖截图...")
            texts = recognize_with_easyocr(image_path)
            # 将 OCR 文字转为食物描述
            for text in texts:
                parsed = parse_text_input(text)
                raw_items.extend(parsed)

    elif args.text:
        logger.info("解析文字输入...")
        raw_items = parse_text_input(args.text)

    if not raw_items:
        result = {
            "success": False,
            "error": "未能识别到食物，请尝试文字描述或更换图片",
            "meal_type": args.meal_type,
            "date": args.date
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    # 查询每种食物的热量
    logger.info(f"查询 {len(raw_items)} 种食物的热量...")
    items_with_nutrition = process_food_items(raw_items)

    # 计算总营养
    total_calories = sum(item.get('calories', 0) for item in items_with_nutrition)
    total_protein = sum(item.get('protein_g') or 0 for item in items_with_nutrition)
    total_carbs = sum(item.get('carbs_g') or 0 for item in items_with_nutrition)
    total_fat = sum(item.get('fat_g') or 0 for item in items_with_nutrition)

    user_message = format_user_message(items_with_nutrition, args.meal_type, total_calories)

    result = {
        "success": True,
        "meal_type": args.meal_type,
        "date": args.date,
        "items": items_with_nutrition,
        "total_calories": total_calories,
        "total_protein_g": round(total_protein, 1),
        "total_carbs_g": round(total_carbs, 1),
        "total_fat_g": round(total_fat, 1),
        "user_message": user_message
    }

    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    print(output_json)

    if args.output:
        output_path = os.path.expanduser(args.output)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_json)
        logger.info(f"结果已保存至：{output_path}")


if __name__ == '__main__':
    main()
