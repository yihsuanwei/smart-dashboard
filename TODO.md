# TODO


---

<!-- 在這裡寫你想改的功能，格式隨意 -->

## 1. Goal Setting
> - 讓user 考慮淡旺季去調整 YoY
> - mtd_sa_revenue_usd
mtd_sp_revenue_usd
mtd_sb_revenue_usd
mtd_sd_revenue_usd
mtd_sa_attributed_ops_usd
mtd_sp_attributed_ops_usd
mtd_sb_attributed_ops_usd
mtd_sd_attributed_ops_usd
## 2. B2B
補充B2B Logic那一筆
建議的分析方法
方法1：ASIN Level B2B佔比（ASIN自身的B2B傾向）

計算：ASIN的B2B銷售額 / ASIN總銷售額(B2B+B2C)
優點：直接反映該ASIN在B2B市場的接受度和潛力
適用：識別哪些產品本身就具有B2B屬性
方法3：ASIN在帳號B2B業務中的重要性

計算：ASIN的B2B銷售額 / Account Level總B2B銷售額
優點：了解該ASIN對帳號B2B業務的貢獻度
適用：優先投資已有B2B表現的核心產品
方法2的局限性 (目前使用此分析方式)

計算：ASIN的B2B銷售額 / Account Level總銷售額(B2B+B2C)
這個指標較難解讀，因為混合了ASIN層級和帳號層級的數據
最佳實踐建議
建議同時使用方法1和方法3：

方法1篩選出B2B佔比高的ASIN（如>30%）→ 產品本身有B2B潛力
方法3識別對帳號B2B業務貢獻大的ASIN → 值得加大投資
額外考量：ASIN的絕對B2B銷售額、YoY成長率
## 3. B2B