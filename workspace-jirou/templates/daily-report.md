# 📊 健康日报模板

> 使用说明：将此模板复制后替换对应变量，生成实际日报。
> 变量格式：`{{变量名}}`

---

📊 {{YEAR}}年{{MONTH}}月{{DAY}}日 {{WEEKDAY}} 健康日报

## ⚖️ 身体数据
  - 体重: {{WEIGHT_MORNING}} kg（晨）/ {{WEIGHT_EVENING}} kg（晚）
  - 体脂: {{BODY_FAT_MORNING}}%（晨）/ {{BODY_FAT_EVENING}}%（晚）
  - 肌肉：{{MUSCLE_RATE_MORNING}}%（晨）/ {{MUSCLE_RATE_EVENING}}%（晚）
  - 储肌能力：{{MUSCLE_LEVEL_MORNING}}（晨）/ {{MUSCLE_LEVEL_EVENING}}（晚）
  - 内脏脂肪：{{VISCERAL_FAT_MORNING}}（晨）/ {{VISCERAL_FAT_EVENING}}（晚）
  - 水分：{{WATER_MORNING}}%（晨）/ {{WATER_EVENING}}%（晚）
  - 蛋白质：{{PROTEIN_MORNING}}%（晨）/ {{PROTEIN_EVENING}}%（晚）
  - 骨量：{{BONE_MASS_MORNING}} kg（晨）/ {{BONE_MASS_EVENING}} kg（晚）
  - 静息心率: {{RESTING_HR}} bpm
  - HRV: {{HRV}} ms
  - BMR: {{BMR}} kcal
  - 最大摄氧量: -

## 😴 睡眠情况
  - 得分: {{SLEEP_SCORE}}
  - 时长: {{SLEEP_DURATION}}
  - 阶段：深睡{{SLEEP_DEEP}} / 浅睡{{SLEEP_LIGHT}} / REM {{SLEEP_REM}} / 清醒{{SLEEP_AWAKE}}

## 🔥 热量情况
  - 总摄入: ~{{TOTAL_INTAKE}} kcal
  - 总消耗: {{TOTAL_BURNED}} kcal
  - 缺口: {{CALORIE_DIFF}} kcal（{{CALORIE_STATUS}}）

### 🍽️ 昨日摄入
  - 早餐：
    {{BREAKFAST_ITEMS}}
    小计：{{BREAKFAST_CALORIES}} kcal
  - 午餐：
    {{LUNCH_ITEMS}}
    小计：{{LUNCH_CALORIES}} kcal
  - 晚餐：
    {{DINNER_ITEMS}}
    小计：{{DINNER_CALORIES}} kcal
  - 零食：{{SNACK_SUMMARY}}

### 💪 昨日消耗
#### 🏃 日常活动（支出1）
  - 步数: {{STEPS}}
  - 距离: {{DISTANCE}}
  - 活动消耗: {{ACTIVE_CALORIES}} kcal

#### 🏋️ 昨日运动（支出2）
  - 运动类型：{{EXERCISE_NAME}}
  - 运动时长：{{EXERCISE_DURATION}}
  - 运动消耗：{{EXERCISE_CALORIES}} kcal
  - 平均心率：{{EXERCISE_AVG_HR}} bpm
  - 最大心率：{{EXERCISE_MAX_HR}} bpm

*消耗 = 支出1 + 支出2 = {{TOTAL_BURNED}} kcal
