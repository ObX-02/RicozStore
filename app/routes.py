from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import get_db_connection
from datetime import datetime, timezone
from app.ai_service import ask_ai
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template("marketing/home.html")


@main_bp.route("/pricing")
def pricing():
    return render_template("marketing/pricing.html")


@main_bp.route("/enterprise")
def enterprise():
    return render_template("marketing/enterprise.html")


@main_bp.route("/products")
def products():
    return render_template("marketing/products.html")


@main_bp.route("/solutions")
def solutions():
    return render_template("marketing/solutions.html")


@main_bp.route("/resources")
def resources():
    return render_template("marketing/resources.html")


@main_bp.route("/blog")
def blog():
    return render_template("marketing/blog.html")


@main_bp.route("/about")
def about():
    return render_template("marketing/about.html")


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        inquiry_type = request.form.get(
            "inquiry_type",
            ""
        ).strip()

        subject = request.form.get(
            "subject",
            ""
        ).strip()

        message = request.form.get(
            "message",
            ""
        ).strip()

        if not name or not email or not subject or not message:

            return render_template(
                "marketing/contact.html",
                error=(
                    "Please complete all required fields."
                ),
                form_data=request.form,
            )

        return render_template(
            "marketing/contact.html",
            success=True,
            form_data={},
        )

    return render_template(
        "marketing/contact.html"
    )

@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter your email and password.", "error")
            return redirect(url_for("main.login"))

        try:
            with get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id, name, email, password_hash, is_active
                        FROM users
                        WHERE LOWER(email) = %s
                        LIMIT 1
                        """,
                        (email,),
                    )

                    user = cursor.fetchone()

        except Exception as error:
            print("LOGIN DATABASE ERROR:", error)

            flash(
                "Unable to connect to the account database.",
                "error",
            )

            return redirect(url_for("main.login"))

        if not user:
            flash("Invalid email or password.", "error")
            return redirect(url_for("main.login"))

        if not user["is_active"]:
            flash(
                "This account is currently inactive.",
                "error",
            )

            return redirect(url_for("main.login"))

        if not check_password_hash(
            user["password_hash"],
            password,
        ):
            flash("Invalid email or password.", "error")
            return redirect(url_for("main.login"))

        session.clear()

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]

        return redirect(url_for("main.dashboard"))

    return render_template("auth/login.html")

# ============================================================
# LEGAL & TRUST
# ============================================================

@main_bp.route("/privacy")
def privacy():
    return render_template(
        "marketing/privacy.html"
    )


@main_bp.route("/terms")
def terms():
    return render_template(
        "marketing/terms.html"
    )


@main_bp.route("/security")
def security():
    return render_template(
        "marketing/security.html"
    )
@main_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash(
                "Please complete all required fields.",
                "error",
            )

            return redirect(url_for("main.signup"))

        if password != confirm_password:
            flash(
                "Passwords do not match.",
                "error",
            )

            return redirect(url_for("main.signup"))

        if len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "error",
            )

            return redirect(url_for("main.signup"))

        try:
            with get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id
                        FROM users
                        WHERE LOWER(email) = %s
                        LIMIT 1
                        """,
                        (email,),
                    )

                    existing_user = cursor.fetchone()

                    if existing_user:
                        flash(
                            "An account with this email already exists.",
                            "error",
                        )

                        return redirect(
                            url_for("main.signup")
                        )

                    password_hash = generate_password_hash(
                        password
                    )

                    
                    cursor.execute(
                        """
                        INSERT INTO users (
                            name,
                            email,
                            password_hash
                        )
                        VALUES (%s, %s, %s)
                        RETURNING id
                        """,
                        (
                            name,
                            email,
                            password_hash,
                        ),
                    )

                    new_user = cursor.fetchone()
                    user_id = new_user["id"]

                    base_slug = "".join(
                        character.lower()
                        if character.isalnum()
                        else "-"
                        for character in name
                    ).strip("-")

                    while "--" in base_slug:
                        base_slug = base_slug.replace("--", "-")

                    base_slug = base_slug[:140].strip("-")
                    base_slug = base_slug or "my-store"

                    store_slug = f"{base_slug}-{user_id}"

                    cursor.execute(
                        """
                        INSERT INTO stores (
                            owner_id,
                            name,
                            slug,
                            currency,
                            timezone,
                            is_active
                        )
                        VALUES (%s, %s, %s, 'PKR', 'Asia/Karachi', TRUE)
                        """,
                        (
                            user_id,
                            f"{name}'s Store",
                            store_slug,
                        ),
                    )

                connection.commit()

        except Exception as error:
            print("SIGNUP DATABASE ERROR:", error)

            flash(
                "Something went wrong while creating your account.",
                "error",
            )

            return redirect(
                url_for("main.signup")
            )

        session.clear()

        session["user_id"] = new_user["id"]
        session["user_name"] = name
        session["user_email"] = email

        flash(
            "Account created successfully.",
            "success",
        )

        return redirect(
            url_for("main.dashboard")
        )

    return render_template("auth/signup.html")


@main_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(
            url_for("main.login")
        )

    return render_template(
        "dashboard/index.html"
    )


@main_bp.route("/logout")
def logout():
    session.clear()

    flash(
        "You have been logged out successfully.",
        "success",
    )

    return redirect(
        url_for("main.home")
    )
@main_bp.route("/dashboard/products")
def dashboard_products():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    s.id,
                    s.name,
                    s.currency
                FROM stores s
                WHERE s.owner_id = %s
                  AND s.is_active = TRUE
                ORDER BY s.id
                LIMIT 1
                """,
                (session["user_id"],),
            )

            store = cur.fetchone()

            if not store:

                flash(
                    "Please create your store before viewing products.",
                    "warning",
                )

                return redirect(
                    url_for("main.dashboard")
                )

            cur.execute(
                """
                SELECT
                    p.id,
                    p.name,
                    p.slug,
                    p.description,
                    p.brand,
                    p.sku,
                    p.price,
                    p.compare_at_price,
                    p.cost_price,
                    p.stock_quantity,
                    p.low_stock_threshold,
                    p.status,
                    p.is_published,
                    p.created_at,
                    p.updated_at
                FROM products p
                WHERE p.store_id = %s
                ORDER BY p.created_at DESC
                """,
                (store["id"],),
            )

            products = cur.fetchall()

            return render_template(
                "dashboard/products.html",
                store=store,
                products=products,
            )

    finally:

        conn.close()

@main_bp.route("/dashboard/products/new", methods=["GET", "POST"])
def create_product():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    user_id = session["user_id"]

    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT id, name
                    FROM stores
                    WHERE owner_id = %s
                    AND is_active = TRUE
                    LIMIT 1
                    """,
                    (user_id,),
                )

                store = cursor.fetchone()

                if not store:
                    flash(
                        "Please set up your store before adding products.",
                        "error",
                    )

                    return redirect(
                        url_for("main.dashboard")
                    )

                cursor.execute(
                    """
                    SELECT id, name
                    FROM categories
                    WHERE store_id = %s
                    AND is_active = TRUE
                    ORDER BY name ASC
                    """,
                    (store["id"],),
                )

                categories = cursor.fetchall()

    except Exception as error:
        print("PRODUCT CREATE DATABASE ERROR:", error)

        flash(
            "Unable to load product information.",
            "error",
        )

        return redirect(
            url_for("main.dashboard_products")
        )

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        brand = request.form.get("brand", "").strip()
        sku = request.form.get("sku", "").strip()

        price = request.form.get(
            "price",
            "0",
        ).strip()

        compare_at_price = request.form.get(
            "compare_at_price",
            "",
        ).strip()

        cost_price = request.form.get(
            "cost_price",
            "",
        ).strip()

        stock_quantity = request.form.get(
            "stock_quantity",
            "0",
        ).strip()

        low_stock_threshold = request.form.get(
            "low_stock_threshold",
            "5",
        ).strip()

        category_id = request.form.get(
            "category_id",
            "",
        ).strip()

        status = request.form.get(
            "status",
            "Draft",
        ).strip()

        is_published = request.form.get(
            "is_published"
        ) == "on"

        if not name:
            flash(
                "Product name is required.",
                "error",
            )

            return redirect(
                url_for("main.create_product")
            )

        slug = name.lower()
        slug = slug.replace(" ", "-")

        try:
            with get_db_connection() as connection:
                with connection.cursor() as cursor:

                    cursor.execute(
                        """
                        SELECT id
                        FROM products
                        WHERE store_id = %s
                        AND slug = %s
                        LIMIT 1
                        """,
                        (
                            store["id"],
                            slug,
                        ),
                    )

                    existing_product = cursor.fetchone()

                    if existing_product:
                        slug = f"{slug}-{store['id']}"

                    cursor.execute(
                        """
                        INSERT INTO products (
                            store_id,
                            name,
                            slug,
                            description,
                            brand,
                            sku,
                            price,
                            compare_at_price,
                            cost_price,
                            stock_quantity,
                            low_stock_threshold,
                            status,
                            is_published,
                            category_id
                        )
                        VALUES (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        )
                        RETURNING id
                        """,
                        (
                            store["id"],
                            name,
                            slug,
                            description or None,
                            brand or None,
                            sku or None,
                            price or 0,
                            compare_at_price or None,
                            cost_price or None,
                            stock_quantity or 0,
                            low_stock_threshold or 5,
                            status or "Draft",
                            is_published,
                            category_id or None,
                        ),
                    )

                    cursor.fetchone()

                connection.commit()

        except Exception as error:
            print("PRODUCT SAVE DATABASE ERROR:", error)

            flash(
                "Unable to save the product.",
                "error",
            )

            return redirect(
                url_for("main.create_product")
            )

        flash(
            "Product created successfully.",
            "success",
        )

        return redirect(
            url_for("main.dashboard_products")
        )

    return render_template(
        "dashboard/product_form.html",
        store=store,
        categories=categories,
    )
@main_bp.route("/dashboard/orders")
def dashboard_orders():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    s.id,
                    s.name,
                    s.currency
                FROM stores s
                WHERE s.owner_id = %s
                  AND s.is_active = TRUE
                ORDER BY s.id
                LIMIT 1
                """,
                (session["user_id"],),
            )

            store = cur.fetchone()

            if not store:
                flash(
                    "Please create your store before viewing orders.",
                    "warning",
                )
                return redirect(url_for("main.dashboard"))

            cur.execute(
                """
                SELECT
                    o.id,
                    o.order_number,
                    o.customer_name,
                    o.customer_email,
                    o.customer_phone,
                    o.subtotal,
                    o.shipping_amount,
                    o.discount_amount,
                    o.total_amount,
                    o.currency,
                    o.payment_status,
                    o.order_status,
                    o.created_at,
                    COUNT(oi.id) AS item_count
                FROM orders o
                LEFT JOIN order_items oi
                    ON oi.order_id = o.id
                WHERE o.store_id = %s
                GROUP BY
                    o.id,
                    o.order_number,
                    o.customer_name,
                    o.customer_email,
                    o.customer_phone,
                    o.subtotal,
                    o.shipping_amount,
                    o.discount_amount,
                    o.total_amount,
                    o.currency,
                    o.payment_status,
                    o.order_status,
                    o.created_at
                ORDER BY o.created_at DESC
                """,
                (store["id"],),
            )

            orders = cur.fetchall()

            cur.execute(
                """
                SELECT
                    COUNT(*) AS total_orders,
                    COUNT(*) FILTER (
                        WHERE order_status IN ('Pending', 'Processing')
                    ) AS pending_orders,
                    COUNT(*) FILTER (
                        WHERE order_status IN ('Completed', 'Delivered')
                    ) AS completed_orders,
                    COALESCE(SUM(total_amount), 0) AS total_revenue
                FROM orders
                WHERE store_id = %s
                """,
                (store["id"],),
            )

            stats = cur.fetchone()

            return render_template(
                "dashboard/orders.html",
                store=store,
                orders=orders,
                stats=stats,
            )

    finally:
        conn.close()
@main_bp.route("/dashboard/inventory")
def dashboard_inventory():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    s.id,
                    s.name,
                    s.currency
                FROM stores s
                WHERE s.owner_id = %s
                  AND s.is_active = TRUE
                ORDER BY s.id
                LIMIT 1
                """,
                (session["user_id"],),
            )

            store = cur.fetchone()

            if not store:

                flash(
                    "Please create your store before viewing inventory.",
                    "warning",
                )

                return redirect(
                    url_for("main.dashboard")
                )

            cur.execute(
                """
                SELECT
                    p.id,
                    p.name,
                    p.brand,
                    p.sku,
                    p.price,
                    p.cost_price,
                    p.stock_quantity,
                    p.low_stock_threshold,
                    p.status,
                    p.is_published,
                    p.created_at
                FROM products p
                WHERE p.store_id = %s
                ORDER BY
                    p.stock_quantity ASC,
                    p.created_at DESC
                """,
                (store["id"],),
            )

            products = cur.fetchall()

            cur.execute(
                """
                SELECT
                    COUNT(*) AS total_products,

                    COALESCE(
                        SUM(p.stock_quantity),
                        0
                    ) AS total_units,

                    COALESCE(
                        SUM(
                            p.stock_quantity *
                            COALESCE(p.cost_price, p.price)
                        ),
                        0
                    ) AS inventory_value,

                    COUNT(*) FILTER (
                        WHERE p.stock_quantity > p.low_stock_threshold
                    ) AS in_stock,

                    COUNT(*) FILTER (
                        WHERE p.stock_quantity > 0
                          AND p.stock_quantity <= p.low_stock_threshold
                    ) AS low_stock,

                    COUNT(*) FILTER (
                        WHERE p.stock_quantity = 0
                    ) AS out_of_stock

                FROM products p

                WHERE p.store_id = %s
                """,
                (store["id"],),
            )

            stats = cur.fetchone()

            return render_template(
                "dashboard/inventory.html",
                store=store,
                products=products,
                stats=stats,
            )

    finally:

        conn.close()

# ============================================================
# CUSTOMERS
# ============================================================

@main_bp.route("/dashboard/customers")
def dashboard_customers():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    s.id,
                    s.name,
                    s.currency
                FROM stores s
                WHERE s.owner_id = %s
                  AND s.is_active = TRUE
                ORDER BY s.id
                LIMIT 1
                """,
                (session["user_id"],),
            )

            store = cur.fetchone()

            if not store:

                flash(
                    "Please create your store before viewing customers.",
                    "warning",
                )

                return redirect(
                    url_for("main.dashboard")
                )

            cur.execute(
                """
                SELECT
                    u.id,
                    u.name,
                    u.email,
                    u.is_active,
                    u.created_at,

                    COUNT(o.id) AS order_count,

                    COALESCE(
                        SUM(o.total_amount),
                        0
                    ) AS total_spent,

                    MAX(o.created_at) AS last_order_at

                FROM users u

                INNER JOIN orders o
                    ON o.customer_user_id = u.id

                WHERE o.store_id = %s

                GROUP BY
                    u.id,
                    u.name,
                    u.email,
                    u.is_active,
                    u.created_at

                ORDER BY
                    last_order_at DESC NULLS LAST,
                    u.created_at DESC
                """,
                (store["id"],),
            )

            customers = cur.fetchall()

            cur.execute(
                """
                SELECT

                    COUNT(DISTINCT o.customer_user_id)
                        FILTER (
                            WHERE o.customer_user_id IS NOT NULL
                        ) AS total_customers,

                    COUNT(DISTINCT o.customer_user_id)
                        FILTER (
                            WHERE o.customer_user_id IS NOT NULL
                            AND o.created_at >= CURRENT_DATE - INTERVAL '30 days'
                        ) AS active_customers,

                    COALESCE(
                        SUM(o.total_amount),
                        0
                    ) AS total_revenue,

                    COUNT(o.id) AS total_orders

                FROM orders o

                WHERE o.store_id = %s
                """,
                (store["id"],),
            )

            stats = cur.fetchone()

            return render_template(
                "dashboard/customers.html",
                store=store,
                customers=customers,
                stats=stats,
            )

    finally:

        conn.close()
# ============================================================
# DISCOUNTS
# ============================================================

@main_bp.route("/dashboard/discounts")
def dashboard_discounts():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    s.id,
                    s.name,
                    s.currency
                FROM stores s
                WHERE s.owner_id = %s
                  AND s.is_active = TRUE
                ORDER BY s.id
                LIMIT 1
                """,
                (session["user_id"],),
            )

            store = cur.fetchone()

            if not store:

                flash(
                    "Please create your store before managing discounts.",
                    "warning",
                )

                return redirect(
                    url_for("main.dashboard")
                )

            cur.execute(
                """
                SELECT
                    d.id,
                    d.name,
                    d.code,
                    d.description,
                    d.discount_type,
                    d.discount_value,
                    d.minimum_order_amount,
                    d.maximum_discount_amount,
                    d.starts_at,
                    d.expires_at,
                    d.usage_limit,
                    d.usage_count,
                    d.is_active,
                    d.created_at

                FROM discounts d

                WHERE d.store_id = %s

                ORDER BY
                    d.created_at DESC
                """,
                (store["id"],),
            )

            discounts = cur.fetchall()

            cur.execute(
                """
                SELECT

                    COUNT(*) AS total_discounts,

                    COUNT(*) FILTER (
                        WHERE is_active = TRUE
                    ) AS active_discounts,

                    COUNT(*) FILTER (
                        WHERE is_active = TRUE
                          AND (
                              expires_at IS NULL
                              OR expires_at > CURRENT_TIMESTAMP
                          )
                    ) AS valid_discounts,

                    COUNT(*) FILTER (
                        WHERE expires_at IS NOT NULL
                          AND expires_at <= CURRENT_TIMESTAMP
                    ) AS expired_discounts

                FROM discounts

                WHERE store_id = %s
                """,
                (store["id"],),
            )

            stats = cur.fetchone()

            return render_template(
                "dashboard/discounts.html",
                store=store,
                discounts=discounts,
                stats=stats,
                current_time=datetime.now(timezone.utc),

            )

    finally:

        conn.close()
# ============================================================
# CREATE DISCOUNT
# ============================================================

@main_bp.route(
    "/dashboard/discounts/new",
    methods=["GET", "POST"]
)
def create_discount():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    s.id,
                    s.name,
                    s.currency
                FROM stores s
                WHERE s.owner_id = %s
                  AND s.is_active = TRUE
                ORDER BY s.id
                LIMIT 1
                """,
                (session["user_id"],),
            )

            store = cur.fetchone()

            if not store:

                flash(
                    "Please create your store before creating discounts.",
                    "warning",
                )

                return redirect(
                    url_for("main.dashboard")
                )

            if request.method == "POST":

                name = request.form.get(
                    "name",
                    ""
                ).strip()

                code = request.form.get(
                    "code",
                    ""
                ).strip().upper()

                description = request.form.get(
                    "description",
                    ""
                ).strip()

                discount_type = request.form.get(
                    "discount_type",
                    "percentage"
                ).strip()

                discount_value = request.form.get(
                    "discount_value",
                    "0"
                ).strip()

                minimum_order_amount = request.form.get(
                    "minimum_order_amount",
                    "0"
                ).strip()

                maximum_discount_amount = request.form.get(
                    "maximum_discount_amount",
                    ""
                ).strip()

                starts_at = request.form.get(
                    "starts_at",
                    ""
                ).strip()

                expires_at = request.form.get(
                    "expires_at",
                    ""
                ).strip()

                usage_limit = request.form.get(
                    "usage_limit",
                    ""
                ).strip()

                is_active = (
                    request.form.get("is_active")
                    == "on"
                )


                if not name:

                    flash(
                        "Discount name is required.",
                        "error"
                    )

                    return redirect(
                        url_for("main.create_discount")
                    )


                if not code:

                    flash(
                        "Discount code is required.",
                        "error"
                    )

                    return redirect(
                        url_for("main.create_discount")
                    )


                if discount_type not in (
                    "percentage",
                    "fixed"
                ):

                    flash(
                        "Invalid discount type.",
                        "error"
                    )

                    return redirect(
                        url_for("main.create_discount")
                    )


                try:

                    discount_value = float(
                        discount_value
                    )

                    minimum_order_amount = float(
                        minimum_order_amount or 0
                    )

                    maximum_discount_amount = (
                        float(maximum_discount_amount)
                        if maximum_discount_amount
                        else None
                    )

                    usage_limit = (
                        int(usage_limit)
                        if usage_limit
                        else None
                    )

                except ValueError:

                    flash(
                        "Please enter valid numeric values.",
                        "error"
                    )

                    return redirect(
                        url_for("main.create_discount")
                    )


                if discount_value <= 0:

                    flash(
                        "Discount value must be greater than zero.",
                        "error"
                    )

                    return redirect(
                        url_for("main.create_discount")
                    )


                if discount_type == "percentage" and discount_value > 100:

                    flash(
                        "Percentage discount cannot exceed 100%.",
                        "error"
                    )

                    return redirect(
                        url_for("main.create_discount")
                    )


                if minimum_order_amount < 0:

                    flash(
                        "Minimum order amount cannot be negative.",
                        "error"
                    )

                    return redirect(
                        url_for("main.create_discount")
                    )


                if (
                    maximum_discount_amount is not None
                    and maximum_discount_amount < 0
                ):

                    flash(
                        "Maximum discount amount cannot be negative.",
                        "error"
                    )

                    return redirect(
                        url_for("main.create_discount")
                    )


                if usage_limit is not None and usage_limit <= 0:

                    flash(
                        "Usage limit must be greater than zero.",
                        "error"
                    )

                    return redirect(
                        url_for("main.create_discount")
                    )


                cur.execute(
                    """
                    SELECT id
                    FROM discounts
                    WHERE store_id = %s
                      AND LOWER(code) = LOWER(%s)
                    LIMIT 1
                    """,
                    (
                        store["id"],
                        code,
                    ),
                )

                existing_discount = cur.fetchone()

                if existing_discount:

                    flash(
                        "This discount code already exists.",
                        "error"
                    )

                    return redirect(
                        url_for("main.create_discount")
                    )


                cur.execute(
                    """
                    INSERT INTO discounts (
                        store_id,
                        name,
                        code,
                        description,
                        discount_type,
                        discount_value,
                        minimum_order_amount,
                        maximum_discount_amount,
                        starts_at,
                        expires_at,
                        usage_limit,
                        is_active
                    )

                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        NULLIF(%s, '')::timestamptz,
                        NULLIF(%s, '')::timestamptz,
                        %s,
                        %s
                    )
                    """,
                    (
                        store["id"],
                        name,
                        code,
                        description or None,
                        discount_type,
                        discount_value,
                        minimum_order_amount,
                        maximum_discount_amount,
                        starts_at,
                        expires_at,
                        usage_limit,
                        is_active,
                    ),
                )

                conn.commit()

                flash(
                    "Discount created successfully.",
                    "success"
                )

                return redirect(
                    url_for("main.dashboard_discounts")
                )


            return render_template(
                "dashboard/discount_form.html",
                store=store,
            )

    finally:

        conn.close()
# ============================================================
# MARKETING
# ============================================================

@main_bp.route("/dashboard/marketing")
def dashboard_marketing():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    s.id,
                    s.name,
                    s.currency
                FROM stores s
                WHERE s.owner_id = %s
                  AND s.is_active = TRUE
                ORDER BY s.id
                LIMIT 1
                """,
                (session["user_id"],),
            )

            store = cur.fetchone()

            if not store:
                flash(
                    "Please create your store before managing marketing.",
                    "warning",
                )
                return redirect(url_for("main.dashboard"))

            cur.execute(
                """
                SELECT
                    COUNT(*) AS total_campaigns
                FROM marketing_campaigns
                WHERE store_id = %s
                """,
                (store["id"],),
            )

            campaign_stats = cur.fetchone()

            cur.execute(
                """
                SELECT
                    COUNT(*) AS active_campaigns
                FROM marketing_campaigns
                WHERE store_id = %s
                  AND status = 'Active'
                """,
                (store["id"],),
            )

            active_stats = cur.fetchone()

            cur.execute(
                """
                SELECT
                    COUNT(*) AS completed_campaigns
                FROM marketing_campaigns
                WHERE store_id = %s
                  AND status = 'Completed'
                """,
                (store["id"],),
            )

            completed_stats = cur.fetchone()

            cur.execute(
                """
                SELECT
                    COALESCE(SUM(budget), 0) AS total_budget
                FROM marketing_campaigns
                WHERE store_id = %s
                """,
                (store["id"],),
            )

            budget_stats = cur.fetchone()

            cur.execute(
                """
                SELECT
                    id,
                    name,
                    campaign_type,
                    description,
                    audience,
                    status,
                    budget,
                    starts_at,
                    ends_at,
                    created_at
                FROM marketing_campaigns
                WHERE store_id = %s
                ORDER BY created_at DESC
                LIMIT 10
                """,
                (store["id"],),
            )

            campaigns = cur.fetchall()

            return render_template(
                "dashboard/marketing.html",
                store=store,
                campaigns=campaigns,
                campaign_stats=campaign_stats,
                active_stats=active_stats,
                completed_stats=completed_stats,
                budget_stats=budget_stats,
            )

    finally:
        conn.close()
# ============================================================
# CREATE MARKETING CAMPAIGN
# ============================================================

@main_bp.route(
    "/dashboard/marketing/new",
    methods=["GET", "POST"]
)
def create_marketing_campaign():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    s.id,
                    s.name,
                    s.currency
                FROM stores s
                WHERE s.owner_id = %s
                  AND s.is_active = TRUE
                ORDER BY s.id
                LIMIT 1
                """,
                (session["user_id"],),
            )

            store = cur.fetchone()

            if not store:
                flash(
                    "Please create your store before creating a campaign.",
                    "warning"
                )
                return redirect(url_for("main.dashboard"))

            if request.method == "POST":

                name = request.form.get(
                    "name",
                    ""
                ).strip()

                campaign_type = request.form.get(
                    "campaign_type",
                    "General"
                ).strip()

                description = request.form.get(
                    "description",
                    ""
                ).strip()

                audience = request.form.get(
                    "audience",
                    "All Customers"
                ).strip()

                status = request.form.get(
                    "status",
                    "Draft"
                ).strip()

                budget = request.form.get(
                    "budget",
                    "0"
                ).strip()

                starts_at = request.form.get(
                    "starts_at",
                    ""
                ).strip()

                ends_at = request.form.get(
                    "ends_at",
                    ""
                ).strip()

                if not name:
                    flash(
                        "Campaign name is required.",
                        "error"
                    )
                    return redirect(
                        url_for(
                            "main.create_marketing_campaign"
                        )
                    )

                allowed_types = (
                    "General",
                    "Email",
                    "Social Media",
                    "Promotion",
                    "Product Launch",
                    "Seasonal",
                    "Flash Sale",
                )

                if campaign_type not in allowed_types:
                    flash(
                        "Invalid campaign type.",
                        "error"
                    )
                    return redirect(
                        url_for(
                            "main.create_marketing_campaign"
                        )
                    )

                allowed_statuses = (
                    "Draft",
                    "Scheduled",
                    "Active",
                    "Completed",
                    "Cancelled",
                )

                if status not in allowed_statuses:
                    flash(
                        "Invalid campaign status.",
                        "error"
                    )
                    return redirect(
                        url_for(
                            "main.create_marketing_campaign"
                        )
                    )

                try:
                    budget = float(budget or 0)
                except ValueError:
                    flash(
                        "Please enter a valid campaign budget.",
                        "error"
                    )
                    return redirect(
                        url_for(
                            "main.create_marketing_campaign"
                        )
                    )

                if budget < 0:
                    flash(
                        "Campaign budget cannot be negative.",
                        "error"
                    )
                    return redirect(
                        url_for(
                            "main.create_marketing_campaign"
                        )
                    )

                if not audience:
                    audience = "All Customers"

                cur.execute(
                    """
                    INSERT INTO marketing_campaigns (
                        store_id,
                        name,
                        campaign_type,
                        description,
                        audience,
                        status,
                        budget,
                        starts_at,
                        ends_at
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        NULLIF(%s, '')::timestamptz,
                        NULLIF(%s, '')::timestamptz
                    )
                    """,
                    (
                        store["id"],
                        name,
                        campaign_type,
                        description or None,
                        audience,
                        status,
                        budget,
                        starts_at,
                        ends_at,
                    ),
                )

                conn.commit()

                flash(
                    "Marketing campaign created successfully.",
                    "success"
                )

                return redirect(
                    url_for(
                        "main.dashboard_marketing"
                    )
                )

            return render_template(
                "dashboard/marketing_form.html",
                store=store,
            )

    finally:
        conn.close()
# ============================================================
# ANALYTICS
# ============================================================

@main_bp.route("/dashboard/analytics")
def dashboard_analytics():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    period = request.args.get(
        "period",
        "30"
    ).strip()

    allowed_periods = (
        "7",
        "30",
        "90",
        "all",
    )

    if period not in allowed_periods:
        period = "30"

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            # ------------------------------------------------
            # ACTIVE STORE
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    s.id,
                    s.name,
                    s.currency
                FROM stores s
                WHERE s.owner_id = %s
                  AND s.is_active = TRUE
                ORDER BY s.id
                LIMIT 1
                """,
                (session["user_id"],),
            )

            store = cur.fetchone()

            if not store:
                flash(
                    "Please create your store before viewing analytics.",
                    "warning"
                )

                return redirect(
                    url_for("main.dashboard")
                )

            # ------------------------------------------------
            # DATE FILTER
            # ------------------------------------------------

            if period == "all":

                date_condition = ""
                date_params = ()

            else:

                days = int(period)

                date_condition = """
                    AND created_at >= CURRENT_TIMESTAMP
                        - (%s * INTERVAL '1 day')
                """

                date_params = (days,)

            # ------------------------------------------------
            # OVERVIEW
            # ------------------------------------------------

            cur.execute(
                f"""
                SELECT
                    COUNT(*) AS total_orders,

                    COALESCE(
                        SUM(total_amount),
                        0
                    ) AS total_revenue,

                    COALESCE(
                        AVG(total_amount),
                        0
                    ) AS average_order_value

                FROM orders

                WHERE store_id = %s

                {date_condition}
                """,
                (
                    store["id"],
                    *date_params,
                ),
            )

            overview = cur.fetchone()

            # ------------------------------------------------
            # PRODUCT STATS
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    COUNT(*) AS total_products,

                    COALESCE(
                        SUM(stock_quantity),
                        0
                    ) AS total_units

                FROM products

                WHERE store_id = %s
                """,
                (store["id"],),
            )

            product_stats = cur.fetchone()

            # ------------------------------------------------
            # CUSTOMERS
            # ------------------------------------------------

            cur.execute(
                f"""
                SELECT
                    COUNT(
                        DISTINCT customer_user_id
                    )
                    FILTER (
                        WHERE customer_user_id IS NOT NULL
                    ) AS total_customers

                FROM orders

                WHERE store_id = %s

                {date_condition}
                """,
                (
                    store["id"],
                    *date_params,
                ),
            )

            customer_stats = cur.fetchone()

            # ------------------------------------------------
            # DAILY SALES
            # ------------------------------------------------

            if period == "all":
                chart_days = 30
            else:
                chart_days = int(period)

            cur.execute(
                """
                SELECT
                    DATE(created_at) AS order_date,

                    COUNT(*) AS order_count,

                    COALESCE(
                        SUM(total_amount),
                        0
                    ) AS revenue

                FROM orders

                WHERE store_id = %s

                  AND created_at >=
                      CURRENT_DATE
                      - (%s * INTERVAL '1 day')

                GROUP BY
                    DATE(created_at)

                ORDER BY
                    order_date ASC

                """,
                (
                    store["id"],
                    chart_days - 1,
                ),
            )

            daily_sales = cur.fetchall()

            # ------------------------------------------------
            # TOP PRODUCTS
            # ------------------------------------------------

            if period == "all":

                cur.execute(
                    """
                    SELECT
                        p.id,
                        p.name,
                        p.price,
                        p.stock_quantity,

                        COALESCE(
                            SUM(oi.quantity),
                            0
                        ) AS units_sold,

                        COALESCE(
                            SUM(oi.total_price),
                            0
                        ) AS product_revenue

                    FROM products p

                    LEFT JOIN order_items oi
                        ON oi.product_id = p.id

                    LEFT JOIN orders o
                        ON o.id = oi.order_id
                       AND o.store_id = p.store_id

                    WHERE p.store_id = %s

                    GROUP BY
                        p.id,
                        p.name,
                        p.price,
                        p.stock_quantity

                    ORDER BY
                        product_revenue DESC,
                        units_sold DESC

                    LIMIT 10
                    """,
                    (store["id"],),
                )

            else:

                cur.execute(
                    """
                    SELECT
                        p.id,
                        p.name,
                        p.price,
                        p.stock_quantity,

                        COALESCE(
                            SUM(oi.quantity),
                            0
                        ) AS units_sold,

                        COALESCE(
                            SUM(oi.total_price),
                            0
                        ) AS product_revenue

                    FROM products p

                    LEFT JOIN order_items oi
                        ON oi.product_id = p.id

                    LEFT JOIN orders o
                        ON o.id = oi.order_id
                       AND o.store_id = p.store_id
                       AND o.created_at >=
                           CURRENT_TIMESTAMP
                           - (%s * INTERVAL '1 day')

                    WHERE p.store_id = %s

                    GROUP BY
                        p.id,
                        p.name,
                        p.price,
                        p.stock_quantity

                    ORDER BY
                        product_revenue DESC,
                        units_sold DESC

                    LIMIT 10
                    """,
                    (
                        int(period),
                        store["id"],
                    ),
                )

            top_products = cur.fetchall()

            # ------------------------------------------------
            # ORDER STATUS
            # ------------------------------------------------

            cur.execute(
                f"""
                SELECT
                    order_status,

                    COUNT(*) AS order_count

                FROM orders

                WHERE store_id = %s

                {date_condition}

                GROUP BY
                    order_status

                ORDER BY
                    order_count DESC
                """,
                (
                    store["id"],
                    *date_params,
                ),
            )

            order_statuses = cur.fetchall()

            # ------------------------------------------------
            # BUSINESS INSIGHTS
            # ------------------------------------------------

            if period == "all":

                previous_period = {
                    "previous_revenue": 0
                }

            else:

                days = int(period)

                cur.execute(
                    """
                    SELECT
                        COALESCE(
                            SUM(total_amount),
                            0
                        ) AS previous_revenue

                    FROM orders

                    WHERE store_id = %s

                      AND created_at >=
                          CURRENT_TIMESTAMP
                          - (%s * INTERVAL '1 day')

                      AND created_at <
                          CURRENT_TIMESTAMP
                          - (%s * INTERVAL '1 day')
                    """,
                    (
                        store["id"],
                        days * 2,
                        days,
                    ),
                )

                previous_period = cur.fetchone()

            # ------------------------------------------------
            # REVENUE GROWTH
            # ------------------------------------------------

            current_revenue = float(
                overview["total_revenue"] or 0
            )

            previous_revenue = float(
                previous_period["previous_revenue"] or 0
            )

            if period == "all":

                revenue_growth = 0

            elif previous_revenue > 0:

                revenue_growth = (
                    (
                        current_revenue
                        - previous_revenue
                    )
                    / previous_revenue
                ) * 100

            elif current_revenue > 0:

                revenue_growth = 100

            else:

                revenue_growth = 0

            # ------------------------------------------------
            # LOW STOCK INTELLIGENCE
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    COUNT(*) AS low_stock_products

                FROM products

                WHERE store_id = %s

                  AND stock_quantity > 0

                  AND stock_quantity <= low_stock_threshold
                """,
                (store["id"],),
            )

            low_stock_stats = cur.fetchone()

            # ------------------------------------------------
            # OUT OF STOCK INTELLIGENCE
            # ------------------------------------------------

            cur.execute(
                """
                SELECT
                    COUNT(*) AS out_of_stock_products

                FROM products

                WHERE store_id = %s

                  AND stock_quantity = 0
                """,
                (store["id"],),
            )

            out_of_stock_stats = cur.fetchone()

            # ------------------------------------------------
            # FINAL ANALYTICS PAGE
            # ------------------------------------------------

            return render_template(
                "dashboard/analytics.html",

                store=store,

                overview=overview,

                product_stats=product_stats,

                customer_stats=customer_stats,

                daily_sales=daily_sales,

                top_products=top_products,

                order_statuses=order_statuses,

                selected_period=period,

                previous_period=previous_period,

                revenue_growth=revenue_growth,

                low_stock_stats=low_stock_stats,

                out_of_stock_stats=out_of_stock_stats,
            )

    finally:

        conn.close()
# ============================================================
# AI STUDIO
# ============================================================

@main_bp.route("/dashboard/ai-studio", methods=["GET", "POST"])
def dashboard_ai_studio():

    if "user_id" not in session:
        return redirect(
            url_for("main.login")
        )

    ai_response = None
    ai_error = None
    user_prompt = ""

    if request.method == "POST":

        user_prompt = request.form.get(
            "prompt",
            ""
        ).strip()

        if not user_prompt:

            ai_error = (
                "Please enter a question or request."
            )

        else:

            system_prompt = """
You are RicozStore AI, an intelligent
e-commerce business assistant.

Help store owners with:
- products
- product descriptions
- marketing
- campaigns
- sales
- customers
- inventory
- SEO
- store growth

Give practical, professional and concise
answers that are useful for an online store.

Do not invent store-specific data unless
the user provides it.
"""

            result = ask_ai(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=800,
            )

            if result["success"]:

                ai_response = result["response"]

            else:

                ai_error = result["error"]

    return render_template(
        "dashboard/ai_studio.html",
        ai_response=ai_response,
        ai_error=ai_error,
        user_prompt=user_prompt,
    )
# ============================================================
# SETTINGS
# ============================================================

@main_bp.route("/dashboard/settings")
def dashboard_settings():

    if "user_id" not in session:
        return redirect(
            url_for("main.login")
        )

    return render_template(
        "dashboard/settings.html"
    )
# ============================================================
# STOREFRONT
# ============================================================

@main_bp.route("/dashboard/storefront")
def dashboard_storefront():

    if "user_id" not in session:
        return redirect(
            url_for("main.login")
        )

    return render_template(
        "dashboard/storefront.html"
    )