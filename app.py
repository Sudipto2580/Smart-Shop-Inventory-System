import streamlit as st
import pandas as pd
import plotly.express as px

from database import get_connection
from allocation import assign_shelf
st.set_page_config(
    page_title="Smart Warehouse Inventory",
    layout="wide"
)   
st.title("🏭 Smart Warehouse Inventory Management System")

# =====================================================
# LOAD DATA
# =====================================================

conn = get_connection()

shelves_df = pd.read_sql_query(
    "SELECT * FROM shelves",
    conn
)

inventory_df = pd.read_sql_query("""
SELECT
inventory.inventory_id,
products.product_name,
inventory.quantity,
inventory.total_weight,
shelves.shelf_name
FROM inventory
LEFT JOIN products
ON inventory.product_id = products.product_id
LEFT JOIN shelves
ON inventory.shelf_id = shelves.shelf_id
""", conn)

transactions_df = pd.read_sql_query(
    "SELECT * FROM transactions",
    conn
)

products_df = pd.read_sql_query(
    "SELECT * FROM products",
    conn
)

categories_df = pd.read_sql_query(
    "SELECT * FROM categories",
    conn
)

conn.close()

# =====================================================
# KPI CARDS
# =====================================================

st.header("📊 Warehouse Overview")

col1, col2, col3, col4 ,col5 = st.columns(5)

with col1:
    st.metric(
        "Products",
        len(products_df)
    )

with col2:
    st.metric(
        "Inventory Records",
        len(inventory_df)
    )

with col3:
    st.metric(
        "Shelves",
        len(shelves_df)
    )

with col4:
    total_capacity = shelves_df["max_capacity"].sum()
    used_capacity = shelves_df["used_capacity"].sum()
    inventory_weight = 0
    if not inventory_df.empty:  
        inventory_weight = inventory_df[
        "total_weight"
    ].sum()

    utilization = 0

    if total_capacity > 0:
        utilization = round(
            (used_capacity / total_capacity) * 100,
            2
        )

    st.metric(
        "Warehouse Usage %",
        utilization
    )
    with st.columns(5)[4]:
        st.metric(
        "Total Capacity",
        f"{total_capacity} kg"
    )
st.divider()

# =====================================================
# ADD PRODUCT MASTER
# =====================================================

st.header("➕ Add Product Master")

conn = get_connection()

product_name = st.text_input(
    "Product Name"
)

category = st.selectbox(
    "Category",
    categories_df["category_name"]
)

weight = st.number_input(
    "Weight Per Item (kg)",
    min_value=1.0,
    value=1.0
)

volume = st.number_input(
    "Volume",
    min_value=1.0,
    value=1.0
)

barcode = st.text_input(
    "Barcode"
)

if st.button("Save Product"):

    if not product_name.strip():

        st.error(
            "Product name cannot be empty."
        )

    else:
        cursor = conn.cursor()
        cursor.execute("""
    SELECT category_id
    FROM categories
    WHERE category_name=?
    """, (category,))

    category_id = cursor.fetchone()[0]
    try:
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
        (?, ?, ?, ?, ?)
        """,
        (
            product_name,
            category_id,
            weight,
            volume,
            barcode
        ))

        conn.commit()

        st.success(
            "Product Added Successfully"
        )

        st.rerun()

    except Exception as e:
        st.error(
            f"Error: {e}"
        )

        
conn.close()

st.divider()

# =====================================================
# ANALYTICS
# =====================================================


st.header("📈 Analytics Dashboard")

# Shelf Usage Chart

fig1 = px.bar(
    shelves_df,
    x="shelf_name",
    y="used_capacity",
    title="Shelf Utilization"
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

# Product Distribution

if not inventory_df.empty:

    fig2 = px.pie(
        inventory_df,
        names="product_name",
        values="quantity",
        title="Inventory Distribution"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

# Transaction Analytics

if not transactions_df.empty:
    action_counts = (
        transactions_df["action"]
        .value_counts()
        .reset_index()
    )

    action_counts.columns = [
        "Action",
        "Count"
    ]

    fig3 = px.bar(
        action_counts,
        x="Action",
        y="Count",
        title="Transactions"
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )
# =====================================================
# INVENTORY ENTRY
# =====================================================

st.header("📦 Add Inventory")

if len(products_df) > 0:
    selected_product = st.selectbox(
        "Select Product",
        products_df["product_name"]
    )

    quantity = st.number_input(
        "Quantity",
        min_value=1,
        value=1
    )

    if st.button("Add Inventory"):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT product_id,
               weight
        FROM products
        WHERE product_name=?
        """,
        (selected_product,)
        )

        product = cursor.fetchone()

        product_id = product[0]
        item_weight = product[1]

        total_weight = item_weight * quantity

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
            (?, ?, ?, ?)
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
            (?, ?, ?, ?)
            """,
            (
                product_id,
                "Added",
                quantity,
                shelf_id
            ))

            cursor.execute("""
            INSERT INTO shelf_allocation_log
            (
            product_id,
            shelf_id
            )
            VALUES
            (?, ?)
            """,
            (
                product_id,
                shelf_id
            ))

            conn.commit()

            st.success(
                f"Allocated to Shelf {shelf_name}"
            )

        else:
            st.error(
                "No shelf has enough capacity."
            )

        conn.close()

st.divider()

# =====================================================
# SHELF UTILIZATION
# =====================================================

st.divider()
st.header("🗄 Shelf Utilization")

for _, row in shelves_df.iterrows():

    utilization = 0

    if row["max_capacity"] > 0:

        utilization = (
            row["used_capacity"] /
            row["max_capacity"]
        )

    st.write(
        f"{row['shelf_name']} "
        f"({row['used_capacity']} / {row['max_capacity']} kg)"
    )

    st.progress(
        float(utilization)
    )

st.divider()

# =====================================================
# WAREHOUSE GRID VIEW
# =====================================================
st.divider()
st.header("🏗 Warehouse Grid View")
rows = ["A", "B", "C", "D"]

for row_name in rows:

    cols = st.columns(4)

    row_data = shelves_df[
        shelves_df["location_row"] == row_name
    ]

    for idx, (_, shelf) in enumerate(
        row_data.iterrows()
    ):

        utilization = (
            shelf["used_capacity"] /
            shelf["max_capacity"]
        )

        percent = round(
            utilization * 100,
            1
        )

        cols[idx].metric(
            shelf["shelf_name"],
            f"{percent}%"
        )

# =====================================================
# INVENTORY TABLE
# =====================================================

st.header("📋 Inventory")

st.dataframe(
    inventory_df,
    use_container_width=True
)

st.divider()

# =====================================================
# SEARCH PRODUCT
# =====================================================

st.header("🔍 Search Product")

search = st.text_input(
    "Search Product"
)

if search:

    result = inventory_df[
        inventory_df["product_name"]
        .str.contains(
            search,
            case=False,
            na=False
        )
    ]

    st.dataframe(
        result,
        use_container_width=True
    )

st.divider()

# =====================================================
# PRODUCT MASTER TABLE
# =====================================================

st.header("📚 Product Master")

st.dataframe(
    products_df,
    use_container_width=True
)

st.divider()

# =====================================================
# REMOVE INVENTORY
# =====================================================

st.header("❌ Remove Inventory")

if not inventory_df.empty:

    remove_product = st.selectbox(
        "Select Product To Remove",
        inventory_df["product_name"].unique()
    )

    remove_qty = st.number_input(
        "Quantity To Remove",
        min_value=1,
        value=1,
        key="remove_qty"
    )

    if st.button("Remove Inventory"):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT inventory_id,
               product_id,
               shelf_id,
               quantity,
               total_weight
        FROM inventory
        WHERE product_id =
        (
            SELECT product_id
            FROM products
            WHERE product_name=?
        )
        """,
        (remove_product,)
        )

        item = cursor.fetchone()

        if item:

            inventory_id = item[0]
            product_id = item[1]
            shelf_id = item[2]
            current_qty = item[3]
            current_weight = item[4]

            if remove_qty <= current_qty:

                weight_per_unit = current_weight / current_qty

                released_weight = (
                    weight_per_unit *
                    remove_qty
                )

                new_qty = current_qty - remove_qty

                new_weight = (
                    current_weight -
                    released_weight
                )

                if new_qty == 0:

                    cursor.execute("""
                    DELETE FROM inventory
                    WHERE inventory_id=?
                    """,
                    (inventory_id,)
                    )

                else:

                    cursor.execute("""
                    UPDATE inventory
                    SET quantity=?,
                        total_weight=?
                    WHERE inventory_id=?
                    """,
                    (
                        new_qty,
                        new_weight,
                        inventory_id
                    ))

                cursor.execute("""
                UPDATE shelves
                SET used_capacity =
                used_capacity - ?
                WHERE shelf_id=?
                """,
                (
                    released_weight,
                    shelf_id
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
                (?, ?, ?, ?)
                """,
                (
                    product_id,
                    "Removed",
                    remove_qty,
                    shelf_id
                ))

                conn.commit()

                st.success(
                    "Inventory Updated Successfully"
                )

            else:

                st.error(
                    "Quantity exceeds inventory."
                )

        conn.close()

        st.rerun()

# =====================================================
# TRANSACTION HISTORY
# =====================================================

st.header("🧾 Transaction History")

st.dataframe(
    transactions_df,
    use_container_width=True
)

#========================================================
# INVENTORY SUMMARY
#========================================================

st.header("📦 Inventory Summary")

st.write(
    f"Total Items: {inventory_df['quantity'].sum()}"
)

st.write(
    f"Total Weight: {inventory_df['total_weight'].sum():.2f} kg"
)