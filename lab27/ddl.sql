CREATE TABLE products(
    products_id SERIAL PRIMARY KEY,
    product_name VARCHAR(50),
    category VARCHAR(50),
    price DECIMAL(10, 2),
    amount INT,
    sale_data DATE
)