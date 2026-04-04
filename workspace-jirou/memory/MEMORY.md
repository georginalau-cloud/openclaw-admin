# 🧠 肌肉 Agent - 长期记忆

## 用户基本信息

```yaml
name: ""                    # 姓名/昵称
gender: ""                  # 性别（male/female）
age: 0                      # 年龄
height_cm: 0                # 身高（cm）
```

---

## 目标设定

```yaml
goal: ""                    # 目标（减脂/增肌/维持体重）
target_weight_kg: 0         # 目标体重（kg）
target_body_fat: 0          # 目标体脂率（%）
deadline: ""                # 目标日期（YYYY-MM-DD）
weekly_weight_loss_kg: 0    # 每周减重目标（kg，减脂期）
```

---

## 最近体重记录（7日移动平均）

| 日期 | 晨重(kg) | 晚重(kg) | 体脂(%) | 肌肉(%) | BMR(kcal) |
|-----|---------|---------|--------|--------|----------|
| - | - | - | - | - | - |

---

## 个人记录

```yaml
lowest_weight_kg: null      # 历史最低体重（kg）
lowest_weight_date: ""      # 历史最低体重日期
lowest_body_fat: null       # 历史最低体脂率（%）
lowest_body_fat_date: ""    # 历史最低体脂率日期
highest_muscle_rate: null   # 历史最高肌肉率（%）
```

---

## 饮食偏好

```yaml
liked_foods: []             # 喜欢/常吃的食物
disliked_foods: []          # 不喜欢/不吃的食物
allergies: []               # 食物过敏项
dietary_restrictions: []    # 饮食限制（素食/清真/低碳等）
typical_meal_size: ""       # 通常饭量（小/中/大）
```

---

## 运动习惯

```yaml
exercise_frequency: ""      # 运动频率（例：每周3-4次）
preferred_exercises: []     # 常做的运动类型
exercise_time: ""           # 通常运动时间（早/晚）
gym_member: false           # 是否有健身房会员
```

---

## 数据偏好设置

```yaml
preferred_weight_unit: "kg"         # 体重单位
preferred_calorie_display: "kcal"   # 热量单位
remind_missed_meals: true           # 是否提醒未记录的餐食
second_reminder_enabled: true       # 是否开启二次提醒
final_reminder_enabled: true        # 是否开启 23:00 最后提醒
report_auto_save: false             # 日报是否自动保存（无需用户确认）
```

---

## 近期备注

```
（在此记录用户的特殊情况、临时调整等）
- 例：2024-01-15 用户出差，可能无法规律饮食
- 例：2024-01-20 开始增肌阶段，热量目标调整为 +300 kcal
```

---

## API 使用统计

```yaml
google_vision_monthly_usage: 0     # 当月 Google Vision API 使用次数（上限 1000）
google_vision_reset_date: ""       # 月度重置日期
last_garmin_sync: ""               # 最后一次 Garmin 数据同步时间
```

---

## 更新记录

| 日期 | 更新内容 |
|-----|--------|
| - | 初始化 MEMORY.md |

---

*此文件由肌肉 Agent 自动维护，每周日更新一次周平均数据。*
*用户可随时要求查看或修改记忆内容。*
