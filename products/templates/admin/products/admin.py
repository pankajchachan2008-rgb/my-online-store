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
            line-height: 1.3;
        }
        .main-box {
            border: 2px solid #000;
            width: 100%;
        }
        td {
            padding: 8px;
            border-bottom: 1px solid #000;
            vertical-align: top;
        }
        .text-center { text-align: center; }
        .fw-bold { font-weight: bold; }
        .title-text { font-size: 15px; font-weight: bold; }
    </style>
</head>
<body>

    {% for order in orders %}
    <table class="main-box" cellpadding="0" cellspacing="0">
        
        <!-- Top Section -->
        <tr>
            <td width="70%" style="border-right: 1px solid #000;">
                <span class="title-text">STANDARD DELIVERY</span><br>
                Partner: Trackon / Shree Maruti
            </td>
            <td width="30%" class="text-center">
                <span class="fw-bold">Prepaid</span><br>
                Date: {{ order.created_at|date:"d-m-Y" }}
            </td>
        </tr>

        <!-- Barcode Section -->
        <tr>
            <td colspan="2" class="text-center" style="padding: 15px;">
                <img src="https://bwipjs-api.metafloor.com/?bcid=code128&text=AWB{{ order.id }}998877&includetext=false" width="220" height="50"><br><br>
                <span class="fw-bold" style="font-size: 14px;">AWB: AWB{{ order.id }}998877</span>
            </td>
        </tr>

        <!-- Address & QR Section -->
        <tr>
            <td width="75%" style="border-right: 1px solid #000;">
                Deliver To:<br>
                <span class="title-text">{{ order.customer_name }}</span><br>
                {{ order.address }}<br>
                <span class="fw-bold">Ph: {{ order.mobile_number }}</span>
            </td>
            <td width="25%" class="text-center">
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=60x60&data=RTE-{{ order.id }}" width="60" height="60"><br>
                <span class="fw-bold">NOH-01</span>
            </td>
        </tr>

        <!-- Bill of Supply (Flat Design, No Nested Table) -->
        <tr>
            <td colspan="2">
                <span class="fw-bold" style="font-size: 12px; text-decoration: underline;">BILL OF SUPPLY</span><br><br>
                <strong>Order ID:</strong> #{{ order.id }} | <strong>Weight:</strong> 0.5 KG<br>
                <strong>Total Amount:</strong> ₹{{ order.total_amount }}<br>
                <i>Do Not Collect Cash (Prepaid Order)</i>
            </td>
        </tr>

        <!-- Footer Section -->
        <tr>
            <td colspan="2" style="border-bottom: 0;">
                Return Address (If Undelivered):<br>
                <strong>Chachan General Store</strong><br>
                Nohar, Rajasthan, India<br>
                Support: support@chachanstore.com
            </td>
        </tr>
    </table>

    <!-- xhtml2pdf native page break tag -->
    {% if not forloop.last %}
        <pdf:nextpage />
    {% endif %}
    
    {% endfor %}

</body>
</html>