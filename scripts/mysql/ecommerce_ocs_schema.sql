-- ============================================================================
-- MySQL E-Commerce OCS Schema
-- Application: E-commerce
-- Run: mysql -u root -h localhost -P 3306 -p < scripts/mysql/ecommerce_ocs_schema.sql
-- ============================================================================

-- ── Database ─────────────────────────────────────────────────────────────────
CREATE DATABASE IF NOT EXISTS ecommerce;
USE ecommerce;

-- ── 1. customers ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

-- ── 2. products ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    product_id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL
) ENGINE=InnoDB;

-- ── 3. orders ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    order_id INT PRIMARY KEY,
    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    order_date DATE NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
) ENGINE=InnoDB;

-- ── Truncate existing data (idempotent re-runs) ─────────────────────────────
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE orders;
TRUNCATE TABLE products;
TRUNCATE TABLE customers;
SET FOREIGN_KEY_CHECKS = 1;

-- ── Insert sample data ──────────────────────────────────────────────────────

-- Customers
INSERT INTO customers (customer_id, name, email, city) VALUES
    (1, 'Rahul',   'rahul@example.com',   'Mumbai'),
    (2, 'Priya',   'priya@example.com',   'Delhi'),
    (3, 'Amit',    'amit@example.com',    'Bangalore'),
    (4, 'Sneha',   'sneha@example.com',   'Chennai'),
    (5, 'Vikram',  'vikram@example.com',  'Hyderabad');

-- Products
INSERT INTO products (product_id, name, category, price, stock) VALUES
    (101, 'Laptop',     'Electronics', 75000.00,  50),
    (102, 'Mouse',      'Electronics',  1500.00, 200),
    (103, 'Keyboard',   'Electronics',  3000.00, 150),
    (104, 'Headphones', 'Electronics',  5000.00, 100),
    (105, 'Notebook',   'Stationery',    200.00, 500);

-- Orders (Rahul bought Laptop and Mouse, matching the MongoDB sample query)
INSERT INTO orders (order_id, customer_id, product_id, quantity, order_date) VALUES
    (1001, 1, 101, 1, '2026-06-15'),
    (1002, 1, 102, 2, '2026-06-16'),
    (1003, 2, 103, 1, '2026-06-16'),
    (1004, 2, 104, 1, '2026-06-17'),
    (1005, 3, 105, 5, '2026-06-17'),
    (1006, 4, 101, 1, '2026-06-18'),
    (1007, 5, 102, 3, '2026-06-18');

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Show all tables
SELECT '── TABLES IN ecommerce ──' AS section;
SHOW TABLES;

-- Show schema of each table
SELECT '── SCHEMA: customers ──' AS section;
DESCRIBE customers;

SELECT '── SCHEMA: products ──' AS section;
DESCRIBE products;

SELECT '── SCHEMA: orders ──' AS section;
DESCRIBE orders;

-- Verify row counts
SELECT '── ROW COUNTS ──' AS section;
SELECT 'customers' AS table_name, count(*) AS row_count FROM customers
UNION ALL
SELECT 'products',  count(*) FROM products
UNION ALL
SELECT 'orders',    count(*) FROM orders;

-- Verify relationships: "What products did Rahul buy?"
SELECT '── SAMPLE QUERY: What products did Rahul buy? ──' AS section;
SELECT
    c.name       AS customer_name,
    p.name       AS product_name,
    o.quantity   AS quantity,
    o.order_date AS order_date
FROM orders AS o
INNER JOIN customers AS c ON o.customer_id = c.customer_id
INNER JOIN products  AS p ON o.product_id  = p.product_id
WHERE c.name = 'Rahul';

-- Full relationship verification: all customers with their orders
SELECT '── ALL CUSTOMER-PRODUCT RELATIONSHIPS ──' AS section;
SELECT
    c.name       AS customer,
    p.name       AS product,
    p.category   AS category,
    o.quantity   AS qty,
    p.price      AS unit_price,
    (o.quantity * p.price) AS total_amount
FROM orders AS o
INNER JOIN customers AS c ON o.customer_id = c.customer_id
INNER JOIN products  AS p ON o.product_id  = p.product_id
ORDER BY c.name, o.order_date;
