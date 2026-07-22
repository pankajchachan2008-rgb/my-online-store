<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Shipping Labels</title>
    <style>
        @page {
            size: 100mm 150mm;
            margin: 5mm;
        }
        body {
            font-family: Helvetica, Arial, sans-serif;
            color: #000000;
            font-size: 11px;
            line-height: 1.2;
        }
        .page-break {
            page-break-after: always;
        }
        /* Yahan se height: 100% hata diya gaya hai taaki PDF engine crash na ho */
        .main-box {
            border: 2px solid #000;
            width: 100%;
        }
        td {
            padding: 6px;
            border-bottom: 1px solid #000;
        }
        .text-center { text-align: center; }
        .fw-bold { font-weight: bold; }
        
        .header-title { font-size: 16px; font-weight: bold; text-transform: uppercase; }
        .awb-text { font-size: 14px; font-weight: bold; letter-spacing: 1px; }
        .section-title { font-size: 9px; text-transform: uppercase; color: #333; margin-bottom: 2px;}
    </style>
</head>
<body>

    {% for order in orders %}
    <table class="main-box" cellpadding="0" cellspacing="0">
        
        <tr>
            <td width="70%" style="border-right: 1px solid #000;">
                <span class="header-title">STANDARD DELIVERY</span><br>
                <span>Partner: Trackon / Shree Maruti</span>
            </td>
            <td width="30%" class="text-center">
                <span style="font-size: 12px;" class="fw-bold">Prepaid</span><br>
                <span style="font-size: 9px;">Date: {{ order.created_at|date:"d-m-Y" }}</span>
            </td>
        </tr>

        <tr>
            <td colspan="2" class="text-center" style="padding: 15px 5px;">
                <img src="https://bwipjs-api.metafloor.com/?bcid=code128&text=AWB{{ order.id }}998877&includetext=false" width="220" height="50"><br>
                <span class="awb-text">AWB: AWB{{ order.id }}998877</span>
            </td>
        </tr>

        <tr>
            <td width="75%" style="border-right: 1px solid #000;">
                <span class="section-title">Deliver To:</span><br>
                <span class="fw-bold" style="font-size: 14px;">{{ order.customer_name }}</span><br>
                <span>{{ order.address }}</span><br>
                <span class="fw-bold">Ph: {{ order.mobile_number }}</span>
            </td>
            <td width="25%" class="text-center" valign="middle">
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=60x60&data=RTE-{{ order.id }}" width="60" height="60"><br>
                <span class="fw-bold" style="font-size: 12px;">NOH-01</span>
            </td>
        </tr>

        <tr>
            <td colspan="2">
                <table width="100%" cellpadding="2" cellspacing="0" style="border: none;">
                    <tr>
                        <td style="border: none; border-bottom: 1px dashed #000; padding: 2px;">
                            <span class="section-title fw-bold">BILL OF SUPPLY</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="border: none; padding: 5px 2px;">
                            <strong>Order ID:</strong> #{{ order.id }} &nbsp;&nbsp;|&nbsp;&nbsp; <strong>Weight:</strong> 0.5 KG<br>
                            <strong>Total Amount:</strong> ₹{{ order.total_amount }}<br>
                            <em>Do Not Collect Cash (Prepaid Order)</em>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>

        <tr>
            <td colspan="2" style="border-bottom: none;">
                <span class="section-title">Return Address (If Undelivered):</span><br>
                <strong>Chachan General Store</strong><br>
                Nohar, Rajasthan, India<br>
                Support: support@chachanstore.com
            </td>
        </tr>
    </table>

    {% if not forloop.last %}
    <div class="page-break"></div>
    {% endif %}
    
    {% endfor %}

</body>
</html>