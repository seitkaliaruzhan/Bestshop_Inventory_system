-- Скрипт создания структуры базы BestShopDB
CREATE DATABASE BestShopDB;
GO
USE BestShopDB;
GO

-- Таблица категорий
CREATE TABLE Category (
    category_id INT IDENTITY PRIMARY KEY,
    category_name NVARCHAR(100) NOT NULL
);

-- Таблица товаров
CREATE TABLE Product (
    product_id INT IDENTITY PRIMARY KEY,
    product_name NVARCHAR(255) NOT NULL,
    category_id INT FOREIGN KEY REFERENCES Category(category_id),
    price DECIMAL(10, 2),
    stock_quantity INT
);