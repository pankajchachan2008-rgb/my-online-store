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
        table {
            width: 100%;
            border-collapse: collapse;
        }
        .main-box {
            border: 2px solid #000;
        }
        td {
            padding: 6px;
            border-bottom: 1px solid #000;
            vertical-align: top;
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
    <table class="main-box">
        
        <tr>
            <td style="width: 70%; border-right: 1px solid #000;">
                <span class="header-title">STANDARD DELIVERY</span><br>
                <span>Partner: Trackon / Shree Maruti</span>
            </td>
            <td style="width: 30%; text-align: center;">
                <span style="font-size: 12px;" class="fw-bold">Prepaid</span><br>
                <span style="font-size: 9px;">Date: {{ order.created_at|date:"d-m-Y" }}</span>
            </td>
        </tr>

        <tr>
            <td colspan="2" style="text-align: center; padding: 15px 5px;">
                <!-- Height/Width ko CSS (style) me move kar diya gaya hai -->
                <img src="https://bwipjs-api.metafloor.com/?bcid=code128&text=AWB{{ order.id }}998877&includetext=false" style="width: 220px; height: 50px;"><br>
                <span class="awb-text">AWB: AWB{{ order.id }}998877</span>
            </td>
        </tr>

        <tr>
            <td style="width: 75%; border-right: 1px solid #000;">
                <span class="section-title">Deliver To:</span><br>
                <span class="fw-bold" style="font-size: 14px;">{{ order.customer_name }}</span><br>
                <span>{{ order.address }}</span><br>
                <span class="fw-bold">Ph: {{ order.mobile_number }}</span>
            </td>
            <td style="width: 25%; text-align: center; vertical-align: middle;">
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=60x60&data=RTE-{{ order.id }}" style="width: 60px; height: 60px;"><br>
                <span class="fw-bold" style="font-size: 12px;">NOH-01</span>
            </td>
        </tr>

        <tr>
            <!-- Cellpadding ki jagah CSS padding: 0 lagaya hai -->
            <td colspan="2" style="padding: 0;">
                <table style="width: 100%; border: none;">
                    <tr>
                        <td style="border: none; border-bottom: 1px dashed #000; padding: 4px;">
                            <span class="section-title fw-bold">BILL OF SUPPLY</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="border: none; padding: 6px;">
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