import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2

from database import get_connection
from streamlit_autorefresh import st_autorefresh
from allocation import assign_shelf

st_autorefresh(
    interval=5000,
    key="warehouse_refresh"
)
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

st.sidebar.title("⚙ Settings")

st.session_state.dark_mode = st.sidebar.toggle(
    "🌙 Dark Mode",
    value=st.session_state.dark_mode
)

if st.session_state.dark_mode:

    st.markdown("""
    <style>

    .stApp{
        background-color:#0E1117;
        color:white;
    }

    .metric-card{
        background:#1E1E1E;
        padding:20px;
        border-radius:15px;
        text-align:center;
        box-shadow:0 0 10px rgba(255,255,255,0.1);
    }

    </style>
    """, unsafe_allow_html=True)

else:

    st.markdown("""
    <style>

    .metric-card{
        background:white;
        padding:20px;
        border-radius:15px;
        text-align:center;
        box-shadow:0 0 10px rgba(0,0,0,0.1);
    }

    </style>
    """, unsafe_allow_html=True)

st.sidebar.title("🏭 Smart Warehouse")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Inventory",
        "Products",
        "Analytics",
        "Transactions",
        "Settings"
    ]
)

if page == "Products":

    st.header("📦 Product Master")

    conn = get_connection()
    cursor = conn.cursor()
st.sidebar.divider()

auto_refresh = st.sidebar.toggle(
    "🔄 Auto Refresh",
    value=True
)

if auto_refresh:
    st_autorefresh(
        interval=5000,
        key="auto_refresh"
    )



st.title("🏭 Smart Warehouse Inventory Management System")

st.caption(
    "AI Powered Inventory Tracking & Warehouse Management"
)
conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM products")
products = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM inventory")
inventory = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM shelves")
shelves = cursor.fetchone()[0]

cursor.execute("""
SELECT COALESCE(
SUM(used_capacity),
0
)
FROM shelves
""")

used = cursor.fetchone()[0]

cursor.execute("""
SELECT COALESCE(
SUM(max_capacity),
0
)
FROM shelves
""")

total = cursor.fetchone()[0]

usage = round(
(used / total) * 100,
2
) if total > 0 else 0
col1,col2,col3,col4 = st.columns(4)

with col1:
    st.metric(
        "📦 Products",
        products
    )

with col2:
    st.metric(
        "📋 Inventory",
        inventory
    )

with col3:
    st.metric(
        "🏭 Shelves",
        shelves
    )

with col4:
    st.metric(
        "⚡ Usage %",
        usage
    )

st.subheader("📊 Warehouse Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "📦 Products",
        products
    )

with col2:
    st.metric(
        "📋 Inventory",
        inventory
    )

with col3:
    st.metric(
        "🏭 Shelves",
        shelves
    )

with col4:
    st.metric(
        "⚡ Usage %",
        f"{usage}%"
    )
st.divider()

st.subheader("🏭 Warehouse Heatmap")
cursor.execute("""
SELECT
shelf_name,
used_capacity,
max_capacity
FROM shelves
ORDER BY shelf_name
""")

shelf_data = cursor.fetchall()
heatmap = []

for shelf in shelf_data:

    shelf_name = shelf[0]
    used = shelf[1]
    max_cap = shelf[2]

    pct = (used/max_cap)*100

    if pct < 40:
        status = "🟢"

    elif pct < 80:
        status = "🟡"

    else:
        status = "🔴"

    heatmap.append(
        f"{status} {shelf_name}"
    )

cols = st.columns(4)

for i, shelf in enumerate(heatmap):

    cols[i % 4].info(shelf)
st.divider()

st.subheader("⚠ Inventory Alerts")
cursor.execute("""
SELECT
p.product_name,
COALESCE(SUM(i.quantity),0)
FROM products p
LEFT JOIN inventory i
ON p.product_id=i.product_id
GROUP BY p.product_name
""")

alerts = cursor.fetchall()

low_stock = False

for item in alerts:

    name = item[0]
    qty = item[1]

    if qty < 5:

        low_stock = True

        st.warning(
            f"{name} stock is low ({qty})"
        )

if not low_stock:
    st.success(
        "No low stock alerts"
    )

st.divider()

st.subheader("📈 Shelf Utilization")
df = pd.DataFrame(
    shelf_data,
    columns=[
        "Shelf",
        "Used",
        "Capacity"
    ]
)
fig = px.bar(
    df,
    x="Shelf",
    y="Used",
    title="Shelf Usage"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

with st.expander("➕ Add Product", expanded=True):

    product_name = st.text_input(
        "Product Name"
    )

    cursor.execute("""
    SELECT category_id,
           category_name
    FROM categories
    ORDER BY category_name
    """)

    categories = cursor.fetchall()

    category_dict = {
        row[1]: row[0]
        for row in categories
    }

    category = st.selectbox(
        "Category",
        list(category_dict.keys())
    )

    weight = st.number_input(
        "Weight",
        min_value=0.0
    )

    volume = st.number_input(
        "Volume",
        min_value=0.0
    )

    barcode = st.text_input(
        "Barcode"
    )

    if st.button("Add Product"):

        cursor.execute("""
        INSERT INTO products
        (
            product_name,
            category_id,
            weight,
            volume,
            barcode
        )
        VALUES
        (
            %s,%s,%s,%s,%s
        )
        """,
        (
            product_name,
            category_dict[category],
            weight,
            volume,
            barcode
        ))

        conn.commit()

        st.success(
            "Product Added Successfully"
        )

        st.rerun()

cursor.execute("""
SELECT
p.product_id,
p.product_name,
c.category_name,
p.weight,
p.volume,
p.barcode
FROM products p
LEFT JOIN categories c
ON p.category_id=c.category_id
ORDER BY p.product_id
""")

products_df = pd.DataFrame(
    cursor.fetchall(),
    columns=[
        "ID",
        "Product",
        "Category",
        "Weight",
        "Volume",
        "Barcode"
    ]
)

st.dataframe(
    products_df,
    use_container_width=True
)

st.subheader("🗑 Delete Product")

if not products_df.empty:

    product_to_delete = st.selectbox(
        "Select Product",
        products_df["Product"]
    )

    if st.button("Delete Product"):

        cursor.execute("""
        DELETE FROM products
        WHERE product_name=%s
        """,
        (
            product_to_delete,
        ))

        conn.commit()

        st.success(
            "Product Deleted"
        )

        st.rerun()

if page == "Inventory":

    st.header("📋 Inventory Management")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT
    product_id,
    product_name,
    weight
    FROM products
    ORDER BY product_name
    """)

    products = cursor.fetchall()

    product_dict = {
        p[1]: (p[0], p[2])
        for p in products
    }

    product_name = st.selectbox(
        "Select Product",
        list(product_dict.keys())
    )

    quantity = st.number_input(
        "Quantity",
        min_value=1,
        step=1
    )

    if st.button("📦 Add Inventory"):

        product_id = product_dict[
            product_name
        ][0]

        weight = product_dict[
            product_name
        ][1]

        total_weight = (
            weight * quantity
        )

        shelf_id, shelf_name = assign_shelf(
            total_weight
        )

        if shelf_id:

            cursor.execute("""
            INSERT INTO inventory
                (
                product_id,
                shelf_id,
                quantity,
                total_weight
                )
                VALUES
                (
                    %s,%s,%s,%s
                )
                """,
                (
                    product_id,
                    shelf_id,
                    quantity,
                    total_weight
                ))
            cursor.execute("""
                INSERT INTO transactions
                    (
                        product_id,
                        action,
                        quantity,
                        shelf_id
                    )
                    VALUES
                    (
                        %s,%s,%s,%s
                    )
                    """,
                    (
                        product_id,
                        "ADD",
                        quantity,
                        shelf_id
                    ))
            cursor.execute("""
                    INSERT INTO product_location_history
                    (
                        product_id,
                        shelf_id,
                        quantity
                    )
                    VALUES
                    (
                        %s,%s,%s
                    )
                    """,
                    (
                        product_id,
                        shelf_id,
                        quantity
                    ))
            conn.commit()

            st.success(
                        f"""
                        Product Stored

                        Shelf: {shelf_name}

                        Quantity: {quantity}
                        """
                    )
            st.rerun()
        else:
            st.error(
                    "No Shelf Capacity Available"
                )

    st.divider()

    st.subheader("📦 Current Inventory")
    cursor.execute("""
    SELECT
    p.product_name,
    s.shelf_name,
    i.quantity,
    i.total_weight
    FROM inventory i
    JOIN products p
    ON i.product_id=p.product_id
    JOIN shelves s
    ON i.shelf_id=s.shelf_id
    ORDER BY i.inventory_id DESC
    """)

    inventory_df = pd.DataFrame(
        cursor.fetchall(),
        columns=[
            "Product",
            "Shelf",
            "Quantity",
            "Weight"
        ]
    )

    st.dataframe(
        inventory_df,
        use_container_width=True
    )

    if page == "Transactions":
        st.header("🧾 Transaction History")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT
            p.product_name,
            t.action,
            t.quantity,
            s.shelf_name,
            t.timestamp
        FROM transactions t
        JOIN products p
            ON t.product_id = p.product_id
        JOIN shelves s
            ON t.shelf_id = s.shelf_id
        ORDER BY t.transaction_id DESC
        """)

        df = pd.DataFrame(
            cursor.fetchall(),
            columns=[
                "Product",
                "Action",
                "Quantity",
                "Shelf",
                "Time"
            ]
        )

        st.dataframe(
            df,
            use_container_width=True
        )

    if page == "Inventory":
        st.divider()
        st.subheader("➖ Remove Inventory")
    cursor.execute("""
    SELECT
    inventory_id,
    p.product_name,
    i.quantity,
    s.shelf_name,
    i.total_weight
    FROM inventory i
    JOIN products p
    ON i.product_id=p.product_id
    JOIN shelves s
    ON i.shelf_id=s.shelf_id
    """)

    records = cursor.fetchall()
    inventory_options = {
    f"{r[1]} | Shelf {r[3]} | Qty {r[2]}": r
    for r in records
    }
    selected = st.selectbox(
    "Inventory Record",
    list(inventory_options.keys())
    )
    remove_qty = st.number_input(
    "Remove Quantity",
    min_value=1,
    step=1
    )
    if st.button("Remove Stock"):
        record = inventory_options[selected]

    inventory_id = record[0]
    current_qty = record[2]
    if remove_qty > current_qty:

        st.error(
            "Quantity exceeds stock"
        )

    else:
        new_qty = current_qty - remove_qty

        if new_qty == 0:

            cursor.execute("""
            DELETE FROM inventory
            WHERE inventory_id=%s
            """,
            (inventory_id,))
        else:

            cursor.execute("""
            UPDATE inventory
            SET quantity=%s
            WHERE inventory_id=%s
            """,
            (
                new_qty,
                inventory_id
            ))

    cursor.execute("""
    INSERT INTO transactions
        (
            product_id,
            action,
            quantity,
            shelf_id
        )
        SELECT
            product_id,
            'REMOVE',
            %s,
            shelf_id
        FROM inventory
        WHERE inventory_id=%s
        """,
        (
            remove_qty,
            inventory_id
        ))

    conn.commit()

    st.success(
            "Inventory Updated"
        )

    st.rerun()

    cursor.execute("""
    SELECT
    p.product_name,
    COALESCE(
        SUM(i.quantity),
        0
    )
    FROM products p
    LEFT JOIN inventory i   
    ON p.product_id=i.product_id
    GROUP BY p.product_name
    """)

    critical = []
    warning = []
    for row in cursor.fetchall():

        product = row[0]
        qty = row[1]

    if qty <= 2:

        critical.append(
            f"{product} ({qty})"
        )

    elif qty <= 5:

        warning.append(
            f"{product} ({qty})"
        )

    st.subheader("🚨 Stock Alerts")
    for item in critical:
        st.error(
        f"Critical Stock: {item}"
        )

    if not critical and not warning:

        st.success(
        "All Products Healthy"
        )







