#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
有品智能体重秤 OCR 识别脚本
使用 EasyOCR 识别秤面截图，提取体重、体脂等身体数据

用法：
    python3 ocr_scale.py --image /path/to/scale.jpg
    python3 ocr_scale.py --image /path/to/scale.jpg --output /path/to/result.json
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)


def load_easyocr_reader():
    """初始化 EasyOCR reader，支持中英文"""
    try:
        import easyocr
        model_dir = os.path.expanduser('~/.EasyOCR/')
        logger.info("正在初始化 EasyOCR（首次运行需下载模型）...")
        reader = easyocr.Reader(
            ['ch_sim', 'en'],
            gpu=False,
            model_storage_directory=model_dir
        )
        logger.info("EasyOCR 初始化完成")
        return reader
    except ImportError:
        logger.error("EasyOCR 未安装，请运行：pip3 install easyocr")
        return None
    except Exception as e:
        logger.error(f"EasyOCR 初始化失败：{e}")
        return None


def recognize_image(reader, image_path: str) -> list:
    """
    使用 EasyOCR 识别图片中的文字

    Args:
        reader: EasyOCR reader 对象
        image_path: 图片路径

    Returns:
        识别结果列表，每项为 (坐标, 文字, 置信度)
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件不存在：{image_path}")

    logger.info(f"正在识别图片：{image_path}")
    results = reader.readtext(image_path)
    logger.info(f"识别到 {len(results)} 个文字区域")
    return results


def extract_scale_data(ocr_results: list) -> dict:
    """
    从 OCR 识别结果中提取有品秤数据

    Args:
        ocr_results: EasyOCR 识别结果列表

    Returns:
        包含体重等数据的字典
    """
    # 将所有识别文字合并为一个字符串（方便匹配）
    texts = [text for _, text, conf in ocr_results if conf > 0.3]
    full_text = ' '.join(texts)
    logger.debug(f"合并文字：{full_text}")

    data = {}
    confidences = []

    # 记录各字段的原始识别置信度
    for _, _, conf in ocr_results:
        confidences.append(conf)

    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    # 提取体重（最突出的数字，通常带 kg）
    weight = _extract_weight(texts, full_text)
    if weight is not None:
        data['weight'] = weight

    # 提取体脂率
    body_fat = _extract_percentage(texts, full_text, ['体脂率', '体脂'])
    if body_fat is not None:
        data['body_fat'] = body_fat

    # 提取肌肉率
    muscle_rate = _extract_percentage(texts, full_text, ['肌肉率', '肌肉'])
    if muscle_rate is not None:
        data['muscle_rate'] = muscle_rate

    # 提取内脏脂肪指数
    visceral_fat = _extract_integer(texts, full_text, ['内脏脂肪指数', '内脏脂肪'])
    if visceral_fat is not None:
        data['visceral_fat'] = visceral_fat

    # 提取基础代谢率（BMR）
    bmr = _extract_bmr(texts, full_text)
    if bmr is not None:
        data['bmr'] = bmr

    # 提取水分
    water = _extract_percentage(texts, full_text, ['水分'])
    if water is not None:
        data['water'] = water

    # 提取蛋白质
    protein = _extract_percentage(texts, full_text, ['蛋白质'])
    if protein is not None:
        data['protein'] = protein

    # 提取骨量
    bone_mass = _extract_bone_mass(texts, full_text)
    if bone_mass is not None:
        data['bone_mass'] = bone_mass

    # 提取储肌能力等级
    muscle_level = _extract_muscle_level(texts, full_text)
    if muscle_level is not None:
        data['muscle_level'] = muscle_level

    return data, avg_confidence


def _extract_weight(texts: list, full_text: str):
    """提取体重数值（kg）"""
    # 模式1：直接匹配 "65.5 kg" 或 "65.5kg"
    patterns = [
        r'(\d{2,3}\.?\d*)\s*[Kk][Gg]',
        r'体重\s*[：:]\s*(\d{2,3}\.?\d*)',
        r'(\d{2,3}\.\d+)\s*$',  # 行末的小数
    ]
    for pattern in patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            try:
                val = float(match.group(1))
                if 10 <= val <= 300:  # 合理体重范围
                    return round(val, 1)
            except ValueError:
                pass

    # 模式2：在文字列表中找最大的两位数小数
    for text in texts:
        match = re.match(r'^(\d{2,3}\.\d)$', text.strip())
        if match:
            try:
                val = float(match.group(1))
                if 10 <= val <= 300:
                    return round(val, 1)
            except ValueError:
                pass
    return None


def _extract_percentage(texts: list, full_text: str, keywords: list):
    """提取百分比数值"""
    for kw in keywords:
        # 查找关键词后面的数字
        pattern = rf'{kw}[^\d]*(\d{{1,2}}\.?\d*)'
        match = re.search(pattern, full_text)
        if match:
            try:
                val = float(match.group(1))
                if 0 <= val <= 100:
                    return round(val, 1)
            except ValueError:
                pass

    # 在文字列表中按顺序查找关键词相邻的数字
    for i, text in enumerate(texts):
        if any(kw in text for kw in keywords):
            # 查找后面几个文字中的数字
            for j in range(i + 1, min(i + 4, len(texts))):
                match = re.search(r'(\d{1,2}\.?\d*)\s*%?', texts[j])
                if match:
                    try:
                        val = float(match.group(1))
                        if 0 <= val <= 100:
                            return round(val, 1)
                    except ValueError:
                        pass
    return None


def _extract_integer(texts: list, full_text: str, keywords: list):
    """提取整数值（如内脏脂肪指数）"""
    for kw in keywords:
        pattern = rf'{kw}[^\d]*(\d{{1,2}})'
        match = re.search(pattern, full_text)
        if match:
            try:
                val = int(match.group(1))
                if 1 <= val <= 30:
                    return val
            except ValueError:
                pass

    for i, text in enumerate(texts):
        if any(kw in text for kw in keywords):
            for j in range(i + 1, min(i + 4, len(texts))):
                match = re.match(r'^(\d{1,2})$', texts[j].strip())
                if match:
                    try:
                        val = int(match.group(1))
                        if 1 <= val <= 30:
                            return val
                    except ValueError:
                        pass
    return None


def _extract_bmr(texts: list, full_text: str):
    """提取基础代谢率（kcal，通常为4位数）"""
    patterns = [
        r'基础代谢[率]?[^\d]*(\d{3,4})',
        r'BMR[^\d]*(\d{3,4})',
        r'(\d{3,4})\s*[Kk][Cc][Aa][Ll]',
        r'(\d{3,4})\s*大卡',
    ]
    for pattern in patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            try:
                val = int(match.group(1))
                if 800 <= val <= 4000:
                    return val
            except ValueError:
                pass
    return None


def _extract_bone_mass(texts: list, full_text: str):
    """提取骨量（kg，通常为小数）"""
    patterns = [
        r'骨量[^\d]*(\d+\.?\d*)\s*[Kk][Gg]?',
        r'骨[^\d]*(\d\.\d)',
    ]
    for pattern in patterns:
        match = re.search(pattern, full_text)
        if match:
            try:
                val = float(match.group(1))
                if 0.5 <= val <= 10:
                    return round(val, 1)
            except ValueError:
                pass
    return None


def _extract_muscle_level(texts: list, full_text: str):
    """提取储肌能力等级"""
    levels = ['优秀', '良好', '标准', '偏低', '不足']
    patterns = [
        r'储肌能力[^\u4e00-\u9fff]*([优良标偏不]+[秀好准低足])',
        r'肌肉等级[：:]\s*(\S+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, full_text)
        if match:
            level = match.group(1)
            for lv in levels:
                if lv in level:
                    return lv
            return level

    # 直接在文字列表中查找等级词
    for text in texts:
        for level in levels:
            if level in text:
                return level
    return None


def validate_data(data: dict) -> dict:
    """
    校验提取的数据合理性，超出范围的字段置为 None

    Args:
        data: 提取的原始数据字典

    Returns:
        校验后的数据字典
    """
    ranges = {
        'weight': (10, 300),
        'body_fat': (3, 60),
        'muscle_rate': (20, 70),
        'visceral_fat': (1, 30),
        'bmr': (800, 4000),
        'water': (30, 75),
        'protein': (5, 30),
        'bone_mass': (0.5, 10),
    }

    validated = {}
    for field, value in data.items():
        if field == 'muscle_level':
            validated[field] = value
            continue

        if field in ranges and value is not None:
            min_val, max_val = ranges[field]
            if min_val <= value <= max_val:
                validated[field] = value
            else:
                logger.warning(f"字段 {field} 的值 {value} 超出合理范围 [{min_val}, {max_val}]，已忽略")
        else:
            validated[field] = value

    return validated


def main():
    parser = argparse.ArgumentParser(
        description='有品智能体重秤 OCR 识别工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 ocr_scale.py --image ~/Downloads/scale.jpg
  python3 ocr_scale.py --image scale.jpg --output result.json
        """
    )
    parser.add_argument('--image', required=True, help='秤面截图路径')
    parser.add_argument('--output', help='输出 JSON 文件路径（可选）')
    parser.add_argument('--debug', action='store_true', help='启用调试日志')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # 扩展路径中的 ~
    image_path = os.path.expanduser(args.image)

    # 初始化 OCR
    reader = load_easyocr_reader()
    if reader is None:
        result = {
            "success": False,
            "error": "EasyOCR 初始化失败",
            "confidence": 0.0
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    try:
        # 识别图片
        ocr_results = recognize_image(reader, image_path)

        if not ocr_results:
            result = {
                "success": False,
                "error": "图片中未识别到文字",
                "confidence": 0.0
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(1)

        # 提取数据
        raw_data, avg_confidence = extract_scale_data(ocr_results)

        # 校验数据
        validated_data = validate_data(raw_data)

        # 构建结果
        result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": validated_data,
            "confidence": round(avg_confidence, 3),
            "raw_text": [text for _, text, _ in ocr_results]
        }

        if len(validated_data) == 0:
            result["success"] = False
            result["error"] = "未能识别到有效的秤面数据，请确保图片清晰且完整"

        # 输出结果
        output_json = json.dumps(result, ensure_ascii=False, indent=2)
        print(output_json)

        # 保存到文件
        if args.output:
            output_path = os.path.expanduser(args.output)
            dir_name = os.path.dirname(output_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_json)
            logger.info(f"结果已保存至：{output_path}")

    except FileNotFoundError as e:
        result = {"success": False, "error": str(e), "confidence": 0.0}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)
    except Exception as e:
        logger.error(f"识别失败：{e}", exc_info=True)
        result = {"success": False, "error": f"识别过程出错：{str(e)}", "confidence": 0.0}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    main()
