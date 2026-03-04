// ==UserScript==
// @name         Sales & Traffic Business Report Viewer
// @namespace    http://tampermonkey.net/
// @version      1.5.0
// @description  彈出視窗顯示 Seller 名稱 + 預設 View/Zoom 設定 (3Y 資料範圍)
// @match        https://www.sellercentral.amazon.dev/*
// @grant        none
// @downloadURL  https://update.greasyfork.org/scripts/551929/Sales%20%20Traffic%20Business%20Report%20Viewer.user.js
// @updateURL    https://update.greasyfork.org/scripts/551929/Sales%20%20Traffic%20Business%20Report%20Viewer.meta.js
// ==/UserScript==

(function () {
  'use strict';

  // 主按鈕
  const btn = document.createElement('button');
  btn.textContent = 'Sales and Traffic Business Report';
  Object.assign(btn.style, {
    position: 'fixed',
    top: '102px',
    right: '20px',
    zIndex: 9999,
    padding: '8px 12px',
    background: '#232f3e',
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer'
  });
  document.body.appendChild(btn);

  function deepFindLabel(obj) {
    if (!obj) return null;
    if (typeof obj === 'object') {
      if (obj.label) return obj.label;
      for (const k in obj) {
        const found = deepFindLabel(obj[k]);
        if (found) return found;
      }
    }
    return null;
  }

  function formatDateCell(d) {
    if (d == null || d === '') return d;
    let dt;
    if (!isNaN(d) && String(d).length <= 10) {
      dt = new Date(Number(d) * 1000);
    } else {
      dt = new Date(d);
    }
    if (isNaN(dt)) return d;
    const y = dt.getFullYear();
    const m = String(dt.getMonth() + 1).padStart(2, '0');
    const day = String(dt.getDate()).padStart(2, '0');
    return `${y}/${m}/${day}`;
  }

  function csvEscape(v) {
    if (v == null) return '';
    const s = String(v);
    if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
    return s;
  }

  btn.addEventListener('click', async () => {
    const win = window.open('', '_blank', 'width=1200,height=700,scrollbars=yes');
    win.document.open();
    win.document.write(`<!doctype html>
<html>
<head><meta charset="utf-8"><title>Sales & Traffic Business Report</title></head>
<body style="font-family: Arial, sans-serif;">
  <h2>📊 Sales & Traffic Business Report</h2>
  <div id="topbar"></div>
  <h3 id="seller">🛒 Seller: (loading...)</h3>
  <div id="settings">⚙️ View: By Month；Zoom: 3Y</div>
  <div id="status">Loading data...</div>
  <div id="table"></div>
</body>
</html>`);
    win.document.close();

    const $ = (id) => win.document.getElementById(id);

    try {
      // Seller
      const sellerRes = await fetch('https://www.sellercentral.amazon.dev/account-switcher/global-and-regional-account/merchantMarketplace?', {
        method: 'GET',
        credentials: 'include',
        headers: { accept: 'application/json' }
      });
      const sellerJson = await sellerRes.json();
      const sellerName = deepFindLabel(sellerJson) || 'UnknownSeller';
      $('seller').textContent = `🛒 Seller: ${sellerName}`;

      // 計算 3Y 範圍（改成 3 年以確保有完整的前年資料）
      const today = new Date();
      const endDate = today.toISOString().split('T')[0];
      const past = new Date(today);
      past.setFullYear(today.getFullYear() - 3);  // 改成 3 年
      const startDate = past.toISOString().split('T')[0];

      // 抓報表
      const repRes = await fetch('https://www.sellercentral.amazon.dev/business-reports/api', {
        method: 'POST',
        credentials: 'include',
        headers: { accept: '*/*', 'content-type': 'application/json' },
        body: JSON.stringify({
          operationName: 'reportDataQuery',
          variables: {
            input: {
              legacyReportId: '102:SalesTrafficTimeSeries',
              granularity: 'MONTH',
              startDate,
              endDate
            }
          },
          query: `query reportDataQuery($input: GetReportDataInput) {
            getReportData(input: $input) {
              columns { label }
              rows
            }
          }`
        })
      });

      // 偵錯：檢查 API 實際返回內容
      const repText = await repRes.text();
      console.log('📊 Sales & Traffic API Response Status:', repRes.status);
      console.log('📊 Sales & Traffic API Response Text:', repText);

      if (!repText || repText.trim() === '') {
        $('status').innerHTML = `❌ API 返回空響應<br>HTTP Status: ${repRes.status}<br>請按 F12 檢查 Console 查看詳細資訊`;
        return;
      }

      let repJson;
      try {
        repJson = JSON.parse(repText);
      } catch (parseErr) {
        $('status').innerHTML = `❌ JSON 解析失敗<br>HTTP Status: ${repRes.status}<br>Response 前 500 字元：<pre style="background:#f5f5f5;padding:10px;overflow:auto;max-height:300px;">${repText.substring(0, 500)}</pre>`;
        return;
      }

      // 檢查是否有 GraphQL 錯誤
      if (repJson.errors && repJson.errors.length > 0) {
        $('status').innerHTML = `❌ API 返回錯誤：<pre style="background:#f5f5f5;padding:10px;overflow:auto;">${JSON.stringify(repJson.errors, null, 2)}</pre>`;
        return;
      }

      const cols = repJson?.data?.getReportData?.columns?.map(c => c.label) || [];
      const rows = repJson?.data?.getReportData?.rows || [];

      if (!cols.length || !rows.length) {
        $('status').innerHTML = `⚠️ 無資料或欄位。<br>API 回應：<pre style="background:#f5f5f5;padding:10px;overflow:auto;max-height:300px;">${JSON.stringify(repJson, null, 2)}</pre>`;
        return;
      }

      const objects = rows.map(r => {
        const obj = {};
        r.forEach((v, i) => {
          const key = cols[i] || `col_${i}`;
          obj[key] = key.toLowerCase().includes('date') ? formatDateCell(v) : v;
        });
        return obj;
      });

      const csvHeader = cols.map(csvEscape).join(',');
      const csvBody = objects.map(row => cols.map(c => csvEscape(row[c])).join(',')).join('\n');
      const csvContent = `${csvHeader}\n${csvBody}`;

      const downloadBtn = win.document.createElement('button');
      downloadBtn.textContent = '💾 Download CSV';
      Object.assign(downloadBtn.style, {
        margin: '8px 0 12px 0',
        padding: '6px 10px',
        background: '#0073bb',
        color: '#fff',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer'
      });

      const y = today.getFullYear();
      const m = String(today.getMonth() + 1).padStart(2, '0');
      const d = String(today.getDate()).padStart(2, '0');
      const safeSeller = sellerName.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_\-]/g, '');
      const fileName = `${y}-${m}-${d}_${safeSeller}_Sales_Traffic_Report.csv`;

      downloadBtn.addEventListener('click', () => {
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = win.document.createElement('a');
        a.href = url;
        a.download = fileName;
        win.document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      });

      $('topbar').appendChild(downloadBtn);

      // Table
      const table = win.document.createElement('table');
      table.style.borderCollapse = 'collapse';
      table.style.fontSize = '14px';
      table.style.width = '100%';

      const thStyle = 'border:1px solid #ddd;padding:6px;background:#f2f2f2;text-align:left;';
      const tdStyle = 'border:1px solid #ddd;padding:6px;';

      const thead = win.document.createElement('thead');
      const trHead = win.document.createElement('tr');
      cols.forEach(c => {
        const th = win.document.createElement('th');
        th.setAttribute('style', thStyle);
        th.textContent = c;
        trHead.appendChild(th);
      });
      thead.appendChild(trHead);
      table.appendChild(thead);

      const tbody = win.document.createElement('tbody');
      objects.forEach((row, ri) => {
        const tr = win.document.createElement('tr');
        cols.forEach(c => {
          const td = win.document.createElement('td');
          td.setAttribute('style', tdStyle + (ri % 2 ? 'background:#fafafa;' : ''));
          td.textContent = row[c];
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);

      $('table').innerHTML = '';
      $('table').appendChild(table);
      $('status').textContent = '';

    } catch (e) {
      $('status').textContent = '❌ 讀取失敗：' + (e && e.message ? e.message : e);
    }
  });
})();
