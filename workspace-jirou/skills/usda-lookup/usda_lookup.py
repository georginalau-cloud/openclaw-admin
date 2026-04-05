#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USDA FoodData Central 查询脚本
查询食物的精确营养成分（热量、蛋白质、碳水、脂肪等）

用法：
    python3 usda_lookup.py --food "brown rice" --weight 250
    python3 usda_lookup.py --food "鸡胸肉" --weight 150
    python3 usda_lookup.py --food "salmon" --list
    python3 usda_lookup.py --id 175167 --weight 200
"""

import argparse
import json
import logging
import os
import sys

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

# USDA API 端点
USDA_SEARCH_URL = 'https://api.nal.usda.gov/fdc/v1/foods/search'
USDA_FOOD_URL = 'https://api.nal.usda.gov/fdc/v1/food/{fdc_id}'

# 中英文食物名称映射（从 food_recognition.py 同步）
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
    '炒饭': 'fried rice',
    '寿司': 'sushi',
    '粥': 'rice porridge congee',
    '燕麦': 'oatmeal cooked',
    '全麦面包': 'bread whole wheat',
    '白面包': 'bread white',
    '土豆': 'potato boiled',
    '红薯': 'sweet potato baked',
    '玉米': 'corn yellow cooked',

    # 肉类
    '鸡胸肉': 'chicken breast cooked',
    '鸡腿': 'chicken thigh cooked',
    '牛肉': 'beef ground cooked',
    '猪肉': 'pork cooked',
    '红烧肉': 'pork belly braised',
    '猪排': 'pork chop cooked',
    '火腿': 'ham cooked',
    '培根': 'bacon cooked',
    '羊肉': 'lamb cooked',
    '鸭肉': 'duck cooked',
    '鸡肉': 'chicken cooked',

    # 海鲜
    '三文鱼': 'salmon cooked',
    '金枪鱼': 'tuna cooked',
    '虾': 'shrimp cooked',
    '螃蟹': 'crab cooked',
    '鱼': 'fish fillet cooked',
    '鲈鱼': 'bass sea cooked',
    '带鱼': 'hairtail fish cooked',
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
    '嫩豆腐': 'tofu soft silken',
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
}

# 目标营养素名称映射
NUTRIENT_MAP = {
    'Energy': 'calories',
    'Protein': 'protein_g',
    'Carbohydrate, by difference': 'carbs_g',
    'Total lipid (fat)': 'fat_g',
    'Fiber, total dietary': 'fiber_g',
    'Sugars, total including NLEA': 'sugar_g',
    'Sodium, Na': 'sodium_mg',
    'Cholesterol': 'cholesterol_mg',
}


def search_food(query: str, api_key: str, page_size: int = 5) -> list:
    """
    搜索食物

    Args:
        query: 搜索关键词
        api_key: USDA API Key
        page_size: 返回结果数量

    Returns:
        食物列表
    """
    try:
        import requests

        response = requests.get(
            USDA_SEARCH_URL,
            params={
                'query': query,
                'api_key': api_key,
                'dataType': ['Foundation', 'SR Legacy', 'Survey (FNDDS)'],
                'pageSize': page_size,
            },
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        return data.get('foods', [])

    except Exception as e:
        logger.error(f"USDA 搜索失败：{e}")
        return []


def get_food_by_id(fdc_id: int, api_key: str) -> dict:
    """
    通过 fdcId 获取食物详情

    Args:
        fdc_id: USDA fdcId
        api_key: USDA API Key

    Returns:
        食物详情字典
    """
    try:
        import requests

        response = requests.get(
            USDA_FOOD_URL.format(fdc_id=fdc_id),
            params={'api_key': api_key},
            timeout=15
        )
        response.raise_for_status()
        return response.json()

    except Exception as e:
        logger.error(f"USDA 获取食物 {fdc_id} 失败：{e}")
        return {}


def parse_nutrients(food_data: dict, weight_g: float) -> dict:
    """
    从食物数据中提取营养成分，按重量计算

    Args:
        food_data: USDA 返回的食物数据
        weight_g: 食物重量（克）

    Returns:
        营养成分字典
    """
    nutrients_raw = {}

    # 兼容搜索结果和详情两种数据格式
    food_nutrients = food_data.get('foodNutrients', [])

    for nutrient in food_nutrients:
        # 搜索结果格式
        name = nutrient.get('nutrientName', '')
        value = nutrient.get('value', 0)

        # 详情格式
        if not name:
            nutrient_obj = nutrient.get('nutrient', {})
            name = nutrient_obj.get('name', '')
            value = nutrient.get('amount', 0)

        if name and value is not None:
            nutrients_raw[name] = value

    # 按重量计算（USDA 数据基于 100g）
    factor = weight_g / 100.0
    result = {'weight_g': weight_g}

    for usda_name, field_name in NUTRIENT_MAP.items():
        raw_value = nutrients_raw.get(usda_name)
        if raw_value is not None:
            calculated = raw_value * factor
            if field_name == 'calories':
                result[field_name] = round(calculated)
            else:
                result[field_name] = round(calculated, 1)

    return result


def lookup_food(food_name: str, weight_g: float) -> dict:
    """
    查询食物营养信息（供其他模块调用）

    Args:
        food_name: 食物名称（中英文均可）
        weight_g: 重量（克）

    Returns:
        营养信息字典
    """
    api_key = os.getenv('USDA_API_KEY', 'DEMO_KEY')

    # 中文转英文
    query = FOOD_NAME_MAP.get(food_name, food_name)
    logger.debug(f"查询：{food_name} → {query}, {weight_g}g")

    foods = search_food(query, api_key, page_size=3)
    if not foods:
        logger.warning(f"USDA 未找到：{query}")
        return {
            'success': False,
            'food_name': food_name,
            'food_name_en': query,
            'weight_g': weight_g,
            'calories': None,
            'source': 'USDA',
            'error': f'未找到食物：{query}'
        }

    food = foods[0]
    nutrients = parse_nutrients(food, weight_g)

    return {
        'success': True,
        'food_name': food_name,
        'food_name_en': food.get('description', query),
        'fdc_id': food.get('fdcId'),
        'weight_g': weight_g,
        'calories': nutrients.get('calories', 0),
        'protein_g': nutrients.get('protein_g', 0),
        'carbs_g': nutrients.get('carbs_g', 0),
        'fat_g': nutrients.get('fat_g', 0),
        'fiber_g': nutrients.get('fiber_g'),
        'sugar_g': nutrients.get('sugar_g'),
        'sodium_mg': nutrients.get('sodium_mg'),
        'source': f"USDA {food.get('dataType', '')}"
    }


def main():
    parser = argparse.ArgumentParser(
        description='USDA FoodData Central 营养查询工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 usda_lookup.py --food "brown rice" --weight 250
  python3 usda_lookup.py --food "鸡胸肉" --weight 150
  python3 usda_lookup.py --food "salmon" --list
  python3 usda_lookup.py --id 175167 --weight 200
        """
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--food', help='食物名称（支持中英文）')
    group.add_argument('--id', type=int, dest='fdc_id', help='USDA fdcId')

    parser.add_argument('--weight', type=float, default=100.0, help='食物重量（克，默认 100g）')
    parser.add_argument('--list', action='store_true', help='列出多个匹配结果')
    parser.add_argument('--debug', action='store_true', help='启用调试日志')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    api_key = os.getenv('USDA_API_KEY', 'DEMO_KEY')
    logger.info(f"使用 API Key：{'DEMO_KEY' if api_key == 'DEMO_KEY' else '***'}")

    if args.fdc_id:
        # 通过 ID 查询
        food_data = get_food_by_id(args.fdc_id, api_key)
        if not food_data:
            result = {"success": False, "error": f"未找到 fdcId: {args.fdc_id}"}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(1)

        nutrients = parse_nutrients(food_data, args.weight)
        result = {
            "success": True,
            "food_name": food_data.get('description', ''),
            "fdc_id": args.fdc_id,
            "weight_g": args.weight,
            **nutrients,
            "source": f"USDA {food_data.get('dataType', '')}"
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.list:
        # 列出多个匹配结果
        query = FOOD_NAME_MAP.get(args.food, args.food)
        foods = search_food(query, api_key, page_size=10)

        if not foods:
            result = {"success": False, "error": f"未找到：{query}"}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(1)

        items = []
        for food in foods:
            items.append({
                "fdc_id": food.get('fdcId'),
                "description": food.get('description'),
                "data_type": food.get('dataType'),
                "brand": food.get('brandOwner', ''),
            })

        result = {
            "success": True,
            "query": args.food,
            "query_en": query,
            "count": len(items),
            "items": items
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        # 标准查询
        result = lookup_food(args.food, args.weight)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result.get('success'):
            sys.exit(1)


if __name__ == '__main__':
    main()
