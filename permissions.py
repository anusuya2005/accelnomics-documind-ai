def allowed_department_ids(conn, user):
    """Read from the database on EVERY request. Never trust a department sent by the browser."""
    if user["role"] == "admin":
        rows = conn.execute("SELECT id FROM departments")
    else:
        rows = conn.execute(
            "SELECT department_id AS id FROM user_departments WHERE user_id = ?", (user["id"],))
    return [row["id"] for row in rows]
