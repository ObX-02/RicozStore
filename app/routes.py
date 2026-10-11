
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
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
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    sc.id,
                    sc.title,
                    sc.slug,
                    sc.excerpt,
                    sc.body,
                    sc.published_at,
                    s.name AS store_name
                FROM store_contents AS sc
                JOIN stores AS s ON s.id = sc.store_id
                WHERE sc.content_type = 'blog'
                  AND sc.status = 'published'
                  AND s.is_active = TRUE
                ORDER BY sc.published_at DESC NULLS LAST, sc.created_at DESC
                """
            )
            posts = cur.fetchall()

        return render_template("marketing/blog.html", posts=posts)

    except Exception:
        current_app.logger.exception("Public blog page failed to load.")
        return render_template("marketing/blog.html", posts=[])

    finally:
        conn.close()


@main_bp.route("/blog/<int:content_id>/<slug>")
def public_blog_post(content_id, slug):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    sc.id,
                    sc.title,
                    sc.slug,
                    sc.excerpt,
                    sc.body,
                    sc.meta_title,
                    sc.meta_description,
                    sc.published_at,
                    s.name AS store_name
                FROM store_contents AS sc
                JOIN stores AS s ON s.id = sc.store_id
                WHERE sc.id = %s
                  AND sc.slug = %s
                  AND sc.content_type = 'blog'
                  AND sc.status = 'published'
                  AND s.is_active = TRUE
                LIMIT 1
                """,
                (content_id, slug),
            )
            post = cur.fetchone()

        if not post:
            return render_template("marketing/blog_detail.html", post=None), 404

        return render_template("marketing/blog_detail.html", post=post)

    except Exception:
        current_app.logger.exception("Public blog article failed to load.")
        return render_template("marketing/blog_detail.html", post=None), 500

    finally:
        conn.close()

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

    search = request.args.get("search", "").strip()
    category_id = request.args.get("category_id", type=int)
    status = request.args.get("status", "").strip()
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)

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
                return redirect(url_for("main.dashboard"))

            cur.execute(
                """
                SELECT
                    id,
                    name
                FROM categories
                WHERE store_id = %s
                ORDER BY name
                """,
                (store["id"],),
            )

            categories = cur.fetchall()

            query = """
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
                    p.category_id,
                    p.created_at,
                    p.updated_at,
                    c.name AS category_name
                FROM products p
                LEFT JOIN categories c
                    ON c.id = p.category_id
                   AND c.store_id = p.store_id
                WHERE p.store_id = %s
            """

            params = [store["id"]]

            if search:
                query += """
                    AND (
                        p.name ILIKE %s
                        OR p.sku ILIKE %s
                        OR COALESCE(p.brand, '') ILIKE %s
                    )
                """

                search_pattern = f"%{search}%"
                params.extend(
                    [
                        search_pattern,
                        search_pattern,
                        search_pattern,
                    ]
                )

            if category_id:
                query += """
                    AND p.category_id = %s
                """
                params.append(category_id)

            if status:
                query += """
                    AND p.status = %s
                """
                params.append(status)

            if min_price is not None:
                query += """
                    AND p.price >= %s
                """
                params.append(min_price)

            if max_price is not None:
                query += """
                    AND p.price <= %s
                """
                params.append(max_price)

            query += """
                ORDER BY p.created_at DESC
            """

            cur.execute(query, tuple(params))

            products = cur.fetchall()

            return render_template(
                "dashboard/products.html",
                store=store,
                products=products,
                categories=categories,
                search=search,
                selected_category=category_id,
                selected_status=status,
                min_price=min_price,
                max_price=max_price,
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
    # ============================================================
# ECOMMERCE FEATURES CENTER
# ============================================================

@main_bp.route("/dashboard/commerce")
def dashboard_commerce():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    features = [
        {
            "title": "Shopping Cart",
            "description": "Manage the shopping journey, cart items, quantities and checkout flow.",
            "category": "Sales",
            "icon": "🛒",
            "status": "Next to implement",
        },
        {
            "title": "Checkout",
            "description": "Customer details, delivery address and order placement.",
            "category": "Sales",
            "icon": "↗",
            "status": "Next to implement",
        },
        {
            "title": "Product Variants",
            "description": "Manage product sizes, colors, variant prices and stock.",
            "category": "Catalog",
            "icon": "◇",
            "status": "Database ready",
        },
        {
            "title": "Shipping & Delivery",
            "description": "Configure shipping zones, delivery methods and shipping charges.",
            "category": "Operations",
            "icon": "➜",
            "status": "Next to implement",
        },
        {
            "title": "Product Reviews",
            "description": "Collect product ratings and customer feedback.",
            "category": "Growth",
            "icon": "☆",
            "status": "Next to implement",
        },
        {
    "title": "Product Image Gallery",
    "description": "Manage product photos, primary images, and accessibility descriptions.",
    "icon": "▧",
    "category": "PRODUCTS",
    "status": "Database ready"
},
        {
            "title": "Wishlist",
            "description": "Allow customers to save products for later.",
            "category": "Growth",
            "icon": "♡",
            "status": "Next to implement",
        },
        {
            "title": "SEO Manager",
            "description": "Manage product metadata, search visibility and store SEO.",
            "category": "Online Store",
            "icon": "⌕",
            "status": "Next to implement",
        },
        {
            "title": "Customer Segments",
            "description": "Organize customer groups for targeted promotions.",
            "category": "Marketing",
            "icon": "◎",
            "status": "Next to implement",
        },
        {
            "title": "Upselling & Recommendations",
            "description": "Suggest related products and increase average order value.",
            "category": "Growth",
            "icon": "↑",
            "status": "Next to implement",
        },
        {
            "title": "Sales Performance",
            "description": "Track revenue, orders, average order value and product performance.",
            "category": "Analytics",
            "icon": "▥",
            "status": "Next to implement",
        },
    ]

    return render_template(
        "dashboard/commerce.html",
        features=features,
    )
    @main_bp.route("/dashboard/cart")
    def dashboard_cart():
        if "user_id" not in session:
            return redirect(url_for("main.login"))

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, currency
                    FROM stores
                    WHERE owner_id = %s AND is_active = TRUE
                    ORDER BY id
                    LIMIT 1
                    """,
                    (session["user_id"],),
                )
                store = cur.fetchone()

                if not store:
                    flash("Please create your store first.", "warning")
                    return redirect(url_for("main.dashboard"))

                cur.execute(
                    """
                    SELECT
                        c.id AS cart_id,
                        c.status,
                        c.created_at,
                        COUNT(ci.id) AS item_count,
                        COALESCE(SUM(ci.quantity), 0) AS total_quantity,
                        COALESCE(SUM(ci.quantity * p.price), 0) AS subtotal
                    FROM shopping_carts c
                    LEFT JOIN shopping_cart_items ci ON ci.cart_id = c.id
                    LEFT JOIN products p
                        ON p.id = ci.product_id
                       AND p.store_id = c.store_id
                    WHERE c.store_id = %s
                    GROUP BY c.id
                    ORDER BY c.created_at DESC
                    LIMIT 100
                    """,
                    (store["id"],),
                )
                carts = cur.fetchall()

                cur.execute(
                    """
                    SELECT
                        COUNT(*) AS total_carts,
                        COUNT(*) FILTER (WHERE status = 'active') AS active_carts,
                        COUNT(*) FILTER (WHERE status = 'converted') AS converted_carts,
                        COUNT(*) FILTER (WHERE status = 'abandoned') AS abandoned_carts
                    FROM shopping_carts
                    WHERE store_id = %s
                    """,
                    (store["id"],),
                )
                stats = cur.fetchone()

        return render_template(
            "dashboard/cart.html",
            store=store,
            carts=carts,
            stats=stats,
        )

    except Exception:
        flash("Unable to load shopping carts. Please check the database setup.", "danger")
        return redirect(url_for("main.dashboard"))
# ============================================================
# PRODUCT VARIANTS
# ============================================================

@main_bp.route("/dashboard/variants", methods=["GET", "POST"])
def dashboard_variants():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, currency
                    FROM stores
                    WHERE owner_id = %s AND is_active = TRUE
                    ORDER BY id
                    LIMIT 1
                    """,
                    (session["user_id"],),
                )
                store = cur.fetchone()

                if not store:
                    flash("Please create your store first.", "warning")
                    return redirect(url_for("main.dashboard"))

                if request.method == "POST":
                    product_id = request.form.get("product_id", type=int)
                    name = request.form.get("name", "").strip()
                    sku = request.form.get("sku", "").strip() or None
                    price = request.form.get("price", type=float)
                    compare_at_price = request.form.get(
                        "compare_at_price", type=float
                    )
                    cost_price = request.form.get("cost_price", type=float)
                    stock_quantity = request.form.get(
                        "stock_quantity", type=int
                    )
                    low_stock_threshold = request.form.get(
                        "low_stock_threshold", default=5, type=int
                    )

                    if (
                        not product_id
                        or not name
                        or price is None
                        or price < 0
                        or stock_quantity is None
                        or stock_quantity < 0
                        or low_stock_threshold is None
                        or low_stock_threshold < 0
                        or (
                            compare_at_price is not None
                            and compare_at_price < 0
                        )
                        or (cost_price is not None and cost_price < 0)
                    ):
                        flash(
                            "Enter a product, variant name and valid non-negative prices and stock values.",
                            "danger",
                        )
                    else:
                        cur.execute(
                            """
                            SELECT id
                            FROM products
                            WHERE id = %s AND store_id = %s
                            """,
                            (product_id, store["id"]),
                        )
                        product = cur.fetchone()

                        if not product:
                            flash("Please select a valid product.", "danger")
                        else:
                            cur.execute(
                                """
                                INSERT INTO product_variants (
                                    product_id,
                                    name,
                                    sku,
                                    price,
                                    compare_at_price,
                                    cost_price,
                                    stock_quantity,
                                    low_stock_threshold
                                )
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                (
                                    product_id,
                                    name,
                                    sku,
                                    price,
                                    compare_at_price,
                                    cost_price,
                                    stock_quantity,
                                    low_stock_threshold,
                                ),
                            )
                            conn.commit()
                            flash("Product variant added successfully.", "success")
                            return redirect(
                                url_for("main.dashboard_variants")
                            )

                cur.execute(
                    """
                    SELECT id, name, sku
                    FROM products
                    WHERE store_id = %s
                    ORDER BY name
                    """,
                    (store["id"],),
                )
                products = cur.fetchall()

                cur.execute(
                    """
                    SELECT
                        v.id,
                        v.name AS variant_name,
                        v.sku AS variant_sku,
                        v.price,
                        v.stock_quantity,
                        v.low_stock_threshold,
                        v.is_active,
                        p.name AS product_name
                    FROM product_variants v
                    JOIN products p ON p.id = v.product_id
                    WHERE p.store_id = %s
                    ORDER BY v.created_at DESC
                    """,
                    (store["id"],),
                )
                variants = cur.fetchall()

        return render_template(
            "dashboard/variants.html",
            store=store,
            products=products,
            variants=variants,
        )

    except Exception:
        flash(
            "Unable to load product variants. Check the database setup.",
            "danger",
        )
        return redirect(url_for("main.dashboard"))
# ============================================================
# PRODUCT REVIEWS & RATINGS
# ============================================================

@main_bp.route("/dashboard/reviews", methods=["GET", "POST"])
def dashboard_reviews():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, currency
                    FROM stores
                    WHERE owner_id = %s AND is_active = TRUE
                    ORDER BY id
                    LIMIT 1
                    """,
                    (session["user_id"],),
                )
                store = cur.fetchone()

                if not store:
                    flash("Please create your store first.", "warning")
                    return redirect(url_for("main.dashboard"))

                if request.method == "POST":
                    review_id = request.form.get("review_id", type=int)
                    new_status = request.form.get("status", "").strip()

                    if not review_id or new_status not in (
                        "approved",
                        "rejected",
                        "pending",
                    ):
                        flash("Invalid review action.", "danger")
                    else:
                        cur.execute(
                            """
                            UPDATE product_reviews AS r
                            SET status = %s, updated_at = CURRENT_TIMESTAMP
                            FROM products AS p
                            WHERE r.id = %s
                              AND r.product_id = p.id
                              AND p.store_id = %s
                            RETURNING r.id
                            """,
                            (new_status, review_id, store["id"]),
                        )
                        updated_review = cur.fetchone()

                        if updated_review:
                            conn.commit()
                            flash(
                                f"Review status updated to {new_status}.",
                                "success",
                            )
                        else:
                            conn.rollback()
                            flash("Review not found in your store.", "warning")

                    return redirect(url_for("main.dashboard_reviews"))

                cur.execute(
                    """
                    SELECT
                        r.id,
                        r.customer_name,
                        r.customer_email,
                        r.rating,
                        r.title,
                        r.review_text,
                        r.status,
                        r.created_at,
                        p.name AS product_name
                    FROM product_reviews r
                    JOIN products p ON p.id = r.product_id
                    WHERE p.store_id = %s
                    ORDER BY
                        CASE r.status
                            WHEN 'pending' THEN 0
                            WHEN 'approved' THEN 1
                            ELSE 2
                        END,
                        r.created_at DESC
                    LIMIT 200
                    """,
                    (store["id"],),
                )
                reviews = cur.fetchall()

                cur.execute(
                    """
                    SELECT
                        COUNT(*) AS total_reviews,
                        COUNT(*) FILTER (
                            WHERE r.status = 'pending'
                        ) AS pending_reviews,
                        COUNT(*) FILTER (
                            WHERE r.status = 'approved'
                        ) AS approved_reviews,
                        COALESCE(AVG(r.rating), 0) AS average_rating
                    FROM product_reviews r
                    JOIN products p ON p.id = r.product_id
                    WHERE p.store_id = %s
                    """,
                    (store["id"],),
                )
                stats = cur.fetchone()

        return render_template(
            "dashboard/reviews.html",
            store=store,
            reviews=reviews,
            stats=stats,
        )

    except Exception:
        flash(
            "Unable to load reviews. Please check the database setup.",
            "danger",
        )
        return redirect(url_for("main.dashboard"))
# ============================================================
# PRODUCT IMAGE GALLERY
# ============================================================

@main_bp.route("/dashboard/product-images", methods=["GET", "POST"])
def dashboard_product_images():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name
                    FROM stores
                    WHERE owner_id = %s AND is_active = TRUE
                    ORDER BY id
                    LIMIT 1
                    """,
                    (session["user_id"],),
                )
                store = cur.fetchone()

                if not store:
                    flash("Please create your store first.", "warning")
                    return redirect(url_for("main.dashboard"))

                if request.method == "POST":
                    action = request.form.get("action", "add").strip()
                    product_id = request.form.get("product_id", type=int)

                    cur.execute(
                        """
                        SELECT id
                        FROM products
                        WHERE id = %s AND store_id = %s
                        """,
                        (product_id, store["id"]),
                    )
                    product = cur.fetchone()

                    if not product:
                        flash("Please select a valid product.", "danger")
                        return redirect(url_for("main.dashboard_product_images"))

                    if action == "delete":
                        image_id = request.form.get("image_id", type=int)

                        cur.execute(
                            """
                            DELETE FROM product_images AS i
                            USING products AS p
                            WHERE i.id = %s
                              AND i.product_id = p.id
                              AND p.store_id = %s
                            RETURNING i.id
                            """,
                            (image_id, store["id"]),
                        )

                        if cur.fetchone():
                            conn.commit()
                            flash("Product image deleted.", "success")
                        else:
                            conn.rollback()
                            flash("Image not found.", "warning")

                    elif action == "primary":
                        image_id = request.form.get("image_id", type=int)

                        cur.execute(
                            """
                            SELECT i.id
                            FROM product_images i
                            JOIN products p ON p.id = i.product_id
                            WHERE i.id = %s
                              AND i.product_id = %s
                              AND p.store_id = %s
                            """,
                            (image_id, product_id, store["id"]),
                        )

                        image = cur.fetchone()

                        if image:
                            cur.execute(
                                """
                                UPDATE product_images
                                SET is_primary = FALSE
                                WHERE product_id = %s
                                """,
                                (product_id,),
                            )
                            cur.execute(
                                """
                                UPDATE product_images
                                SET is_primary = TRUE
                                WHERE id = %s
                                """,
                                (image_id,),
                            )
                            conn.commit()
                            flash("Primary product image updated.", "success")
                        else:
                            conn.rollback()
                            flash("Image not found for this product.", "warning")

                    else:
                        image_url = request.form.get("image_url", "").strip()
                        alt_text = request.form.get("alt_text", "").strip()
                        make_primary = request.form.get("is_primary") == "yes"

                        if not image_url or len(image_url) > 2000:
                            flash("Enter a valid image URL (maximum 2000 characters).", "danger")
                            return redirect(url_for("main.dashboard_product_images"))

                        if not image_url.startswith(("https://", "http://")):
                            flash("Image URL must start with http:// or https://.", "danger")
                            return redirect(url_for("main.dashboard_product_images"))

                        if len(alt_text) > 255:
                            flash("Alt text must be 255 characters or fewer.", "danger")
                            return redirect(url_for("main.dashboard_product_images"))

                        cur.execute(
                            """
                            SELECT COUNT(*) AS image_count
                            FROM product_images
                            WHERE product_id = %s
                            """,
                            (product_id,),
                        )
                        image_count = cur.fetchone()["image_count"]

                        if image_count >= 20:
                            flash("A product can have up to 20 gallery images.", "warning")
                            return redirect(url_for("main.dashboard_product_images"))

                        cur.execute(
                            """
                            SELECT id
                            FROM product_images
                            WHERE product_id = %s AND is_primary = TRUE
                            """,
                            (product_id,),
                        )
                        has_primary = cur.fetchone() is not None

                        if make_primary:
                            cur.execute(
                                """
                                UPDATE product_images
                                SET is_primary = FALSE
                                WHERE product_id = %s
                                """,
                                (product_id,),
                            )

                        cur.execute(
                            """
                            INSERT INTO product_images
                                (product_id, image_url, alt_text, is_primary, sort_order)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (
                                product_id,
                                image_url,
                                alt_text or None,
                                make_primary or not has_primary,
                                image_count,
                            ),
                        )
                        conn.commit()
                        flash("Product image added to gallery.", "success")

                    return redirect(url_for("main.dashboard_product_images"))

                cur.execute(
                    """
                    SELECT id, name
                    FROM products
                    WHERE store_id = %s
                    ORDER BY name
                    """,
                    (store["id"],),
                )
                products = cur.fetchall()

                cur.execute(
                    """
                    SELECT
                        i.id,
                        i.product_id,
                        i.image_url,
                        i.alt_text,
                        i.is_primary,
                        i.sort_order,
                        i.created_at,
                        p.name AS product_name
                    FROM product_images i
                    JOIN products p ON p.id = i.product_id
                    WHERE p.store_id = %s
                    ORDER BY p.name, i.is_primary DESC, i.sort_order, i.id DESC
                    """,
                    (store["id"],),
                )
                images = cur.fetchall()

                cur.execute(
                    """
                    SELECT
                        COUNT(*) AS total_images,
                        COUNT(*) FILTER (WHERE i.is_primary = TRUE) AS primary_images,
                        COUNT(DISTINCT i.product_id) AS products_with_images
                    FROM product_images i
                    JOIN products p ON p.id = i.product_id
                    WHERE p.store_id = %s
                    """,
                    (store["id"],),
                )
                stats = cur.fetchone()

        return render_template(
            "dashboard/product_images.html",
            store=store,
            products=products,
            images=images,
            stats=stats,
        )

    except Exception:
        flash("Unable to load product images. Check the application logs.", "danger")
        return redirect(url_for("main.dashboard"))

@main_bp.route("/dashboard/content", methods=["GET", "POST"])
def dashboard_content():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, currency
                FROM stores
                WHERE owner_id = %s AND is_active = TRUE
                ORDER BY id
                LIMIT 1
                """,
                (session["user_id"],),
            )
            store = cur.fetchone()

            if not store:
                flash("Please create your store before managing content.", "warning")
                return redirect(url_for("main.dashboard"))

            store_id = store["id"]

            if request.method == "POST":
                action = request.form.get("action", "").strip()
                content_id = request.form.get("content_id", type=int)

                if action in ("delete", "publish", "unpublish"):
                    if not content_id:
                        flash("Invalid content selected.", "danger")
                        return redirect(url_for("main.dashboard_content"))

                    if action == "delete":
                        cur.execute(
                            """
                            DELETE FROM store_contents
                            WHERE id = %s AND store_id = %s
                            """,
                            (content_id, store_id),
                        )

                    else:
                        status = "published" if action == "publish" else "draft"
                        cur.execute(
                            """
                            UPDATE store_contents
                            SET status = %s,
                                published_at = CASE
                                    WHEN %s = 'published'
                                    THEN COALESCE(published_at, CURRENT_TIMESTAMP)
                                    ELSE NULL
                                END,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s AND store_id = %s
                            """,
                            (status, status, content_id, store_id),
                        )

                    if cur.rowcount:
                        conn.commit()
                        flash(
                            "Content deleted successfully."
                            if action == "delete"
                            else "Content status updated successfully.",
                            "success",
                        )
                    else:
                        conn.rollback()
                        flash("Content was not found.", "warning")

                    return redirect(url_for("main.dashboard_content"))

                if action in ("create", "update"):
                    title = request.form.get("title", "").strip()
                    slug = request.form.get("slug", "").strip().lower()
                    content_type = request.form.get("content_type", "page").strip()
                    excerpt = request.form.get("excerpt", "").strip()
                    body = request.form.get("body", "").strip()
                    meta_title = request.form.get("meta_title", "").strip()
                    meta_description = request.form.get("meta_description", "").strip()
                    status = request.form.get("status", "draft").strip()

                    if not title or not slug:
                        flash("Title and URL slug are required.", "danger")
                        return redirect(url_for("main.dashboard_content"))

                    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-")
                    if (
                        any(char not in allowed for char in slug)
                        or slug.startswith("-")
                        or slug.endswith("-")
                        or "--" in slug
                    ):
                        flash(
                            "Slug must use lowercase letters, numbers and single hyphens.",
                            "danger",
                        )
                        return redirect(url_for("main.dashboard_content"))

                    if content_type not in ("page", "blog"):
                        flash("Invalid content type.", "danger")
                        return redirect(url_for("main.dashboard_content"))

                    if status not in ("draft", "published"):
                        status = "draft"

                    if action == "create":
                        cur.execute(
                            """
                            INSERT INTO store_contents (
                                store_id, content_type, title, slug,
                                excerpt, body, meta_title, meta_description,
                                status, published_at
                            )
                            VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                CASE WHEN %s = 'published'
                                     THEN CURRENT_TIMESTAMP
                                     ELSE NULL
                                END
                            )
                            """,
                            (
                                store_id,
                                content_type,
                                title,
                                slug,
                                excerpt or None,
                                body,
                                meta_title or None,
                                meta_description or None,
                                status,
                                status,
                            ),
                        )
                        conn.commit()
                        flash("Content created successfully.", "success")

                    else:
                        if not content_id:
                            flash("Invalid content selected for editing.", "danger")
                            return redirect(url_for("main.dashboard_content"))

                        cur.execute(
                            """
                            UPDATE store_contents
                            SET content_type = %s,
                                title = %s,
                                slug = %s,
                                excerpt = %s,
                                body = %s,
                                meta_title = %s,
                                meta_description = %s,
                                status = %s,
                                published_at = CASE
                                    WHEN %s = 'published'
                                    THEN COALESCE(published_at, CURRENT_TIMESTAMP)
                                    ELSE NULL
                                END,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s AND store_id = %s
                            """,
                            (
                                content_type,
                                title,
                                slug,
                                excerpt or None,
                                body,
                                meta_title or None,
                                meta_description or None,
                                status,
                                status,
                                content_id,
                                store_id,
                            ),
                        )

                        if cur.rowcount:
                            conn.commit()
                            flash("Content updated successfully.", "success")
                        else:
                            conn.rollback()
                            flash("Content was not found.", "warning")

                    return redirect(url_for("main.dashboard_content"))

                flash("Unknown content action.", "danger")
                return redirect(url_for("main.dashboard_content"))

            cur.execute(
                """
                SELECT
                    id, content_type, title, slug, excerpt, body,
                    meta_title, meta_description, status,
                    published_at, created_at, updated_at
                FROM store_contents
                WHERE store_id = %s
                ORDER BY updated_at DESC, id DESC
                """,
                (store_id,),
            )
            contents = cur.fetchall()

            cur.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE content_type = 'page') AS pages,
                    COUNT(*) FILTER (WHERE content_type = 'blog') AS blog_posts,
                    COUNT(*) FILTER (WHERE status = 'published') AS published
                FROM store_contents
                WHERE store_id = %s
                """,
                (store_id,),
            )
            stats = cur.fetchone()

        return render_template(
            "dashboard/content.html",
            store=store,
            contents=contents,
            stats=stats,
        )

    except Exception:
        conn.rollback()
        current_app.logger.exception("Dashboard content management failed.")
        flash(
            "Unable to manage content. Check the application logs for details.",
            "danger",
        )
        return redirect(url_for("main.dashboard"))

    finally:
        conn.close()

# MARKETS
@main_bp.route("/dashboard/markets", methods=["GET", "POST"])
def dashboard_markets():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, currency
                FROM stores
                WHERE owner_id = %s AND is_active = TRUE
                ORDER BY id
                LIMIT 1
                """,
                (session["user_id"],),
            )
            store = cur.fetchone()

            if not store:
                flash("Please create your store before managing markets.", "warning")
                return redirect(url_for("main.dashboard"))

            store_id = store["id"]

            if request.method == "POST":
                name = request.form.get("name", "").strip()
                countries_raw = request.form.get("countries", "").strip()
                currency = request.form.get("currency", "USD").strip().upper()
                status = request.form.get("status", "active").strip().lower()
                is_primary = request.form.get("is_primary") == "on"

                countries = [
                    country.strip().upper()
                    for country in countries_raw.split(",")
                    if country.strip()
                ]

                if not name:
                    flash("Market name is required.", "danger")
                elif len(currency) != 3 or not currency.isalpha():
                    flash("Enter a valid three-letter currency code.", "danger")
                elif status not in ("active", "inactive"):
                    flash("Select a valid market status.", "danger")
                else:
                    try:
                        if is_primary:
                            cur.execute(
                                """
                                UPDATE store_markets
                                SET is_primary = FALSE,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE store_id = %s
                                """,
                                (store_id,),
                            )

                        cur.execute(
                            """
                            INSERT INTO store_markets
                                (store_id, name, countries, currency, status, is_primary)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                            (
                                store_id,
                                name,
                                countries,
                                currency,
                                status,
                                is_primary,
                            ),
                        )
                        conn.commit()
                        flash("Market created successfully.", "success")
                        return redirect(url_for("main.dashboard_markets"))
                    except Exception:
                        conn.rollback()
                        current_app.logger.exception("Failed to create market.")
                        flash(
                            "Market could not be created. Check whether its name already exists.",
                            "danger",
                        )

            cur.execute(
                """
                SELECT id, name, countries, currency, status, is_primary,
                       created_at
                FROM store_markets
                WHERE store_id = %s
                ORDER BY is_primary DESC, created_at DESC, id DESC
                """,
                (store_id,),
            )
            markets = cur.fetchall()

        return render_template(
            "dashboard/markets.html",
            store=store,
            markets=markets,
        )
    finally:
        conn.close()

# ============================================================
# GROWTH DASHBOARD
# ============================================================

@main_bp.route("/dashboard/growth")
def dashboard_growth():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    period = request.args.get("period", "30").strip()
    if period not in ("7", "30", "90"):
        period = "30"

    days = int(period)
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, currency
                FROM stores
                WHERE owner_id = %s AND is_active = TRUE
                ORDER BY id
                LIMIT 1
                """,
                (session["user_id"],),
            )
            store = cur.fetchone()

            if not store:
                flash(
                    "Please create your store before viewing Growth.",
                    "warning",
                )
                return redirect(url_for("main.dashboard"))

            store_id = store["id"]

            cur.execute(
                """
                SELECT
                    COUNT(*) AS total_orders,
                    COALESCE(SUM(total_amount), 0) AS revenue,
                    COALESCE(AVG(total_amount), 0) AS average_order_value,
                    COUNT(DISTINCT customer_user_id)
                        FILTER (WHERE customer_user_id IS NOT NULL)
                        AS unique_customers
                FROM orders
                WHERE store_id = %s
                  AND created_at >= CURRENT_TIMESTAMP
                      - (%s * INTERVAL '1 day')
                """,
                (store_id, days),
            )
            current = cur.fetchone()

            cur.execute(
                """
                SELECT
                    COUNT(*) AS total_orders,
                    COALESCE(SUM(total_amount), 0) AS revenue,
                    COUNT(DISTINCT customer_user_id)
                        FILTER (WHERE customer_user_id IS NOT NULL)
                        AS unique_customers
                FROM orders
                WHERE store_id = %s
                  AND created_at >= CURRENT_TIMESTAMP
                      - (%s * INTERVAL '1 day')
                  AND created_at < CURRENT_TIMESTAMP
                      - (%s * INTERVAL '1 day')
                """,
                (store_id, days * 2, days),
            )
            previous = cur.fetchone()

            def growth_rate(now_value, previous_value):
                now_value = float(now_value or 0)
                previous_value = float(previous_value or 0)

                if previous_value > 0:
                    return round(
                        ((now_value - previous_value) / previous_value) * 100,
                        1,
                    )

                if now_value > 0:
                    return None

                return 0.0

            revenue_growth = growth_rate(
                current["revenue"], previous["revenue"]
            )
            orders_growth = growth_rate(
                current["total_orders"], previous["total_orders"]
            )
            customers_growth = growth_rate(
                current["unique_customers"], previous["unique_customers"]
            )

            cur.execute(
                """
                SELECT
                    DATE(created_at) AS order_date,
                    COUNT(*) AS order_count,
                    COALESCE(SUM(total_amount), 0) AS revenue
                FROM orders
                WHERE store_id = %s
                  AND created_at >= CURRENT_DATE
                      - (%s * INTERVAL '1 day')
                GROUP BY DATE(created_at)
                ORDER BY order_date
                """,
                (store_id, days - 1),
            )
            daily_sales = cur.fetchall()

            cur.execute(
                """
                SELECT
                    p.id,
                    p.name,
                    COALESCE(SUM(oi.quantity), 0) AS units_sold,
                    COALESCE(SUM(oi.total_price), 0) AS revenue
                FROM products p
                LEFT JOIN order_items oi ON oi.product_id = p.id
                LEFT JOIN orders o
                    ON o.id = oi.order_id
                   AND o.store_id = p.store_id
                   AND o.created_at >= CURRENT_TIMESTAMP
                       - (%s * INTERVAL '1 day')
                WHERE p.store_id = %s
                GROUP BY p.id, p.name
                ORDER BY revenue DESC, units_sold DESC
                LIMIT 5
                """,
                (days, store_id),
            )
            top_products = cur.fetchall()

            cur.execute(
                """
                SELECT
                    COUNT(*) FILTER (
                        WHERE stock_quantity > 0
                          AND stock_quantity <= low_stock_threshold
                    ) AS low_stock,
                    COUNT(*) FILTER (
                        WHERE stock_quantity = 0
                    ) AS out_of_stock
                FROM products
                WHERE store_id = %s
                """,
                (store_id,),
            )
            inventory = cur.fetchone()

            cur.execute(
                """
                SELECT COUNT(*) AS total_products
                FROM products
                WHERE store_id = %s
                """,
                (store_id,),
            )
            product_stats = cur.fetchone()

        return render_template(
            "dashboard/growth.html",
            store=store,
            period=period,
            current=current,
            previous=previous,
            revenue_growth=revenue_growth,
            orders_growth=orders_growth,
            customers_growth=customers_growth,
            daily_sales=daily_sales,
            top_products=top_products,
            inventory=inventory,
            product_stats=product_stats,
        )
    finally:
        conn.close()