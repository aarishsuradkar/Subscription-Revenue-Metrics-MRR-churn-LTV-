-- ==============================================================================
-- 00_schema_and_load.sql
-- Database Schema Definition & Data Ingestion Script for MySQL 8.0+
-- Project: Subscription Revenue Metrics (MRR, Churn, Cohort Retention, LTV)
--
-- DISCLAIMER: Synthetic data modelled on Stripe-style subscription billing.
-- Not real customer data.
-- ==============================================================================

-- 1. Create Database if not exists
CREATE DATABASE IF NOT EXISTS subscription_analytics
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE subscription_analytics;

-- 2. Drop existing tables if needed (in reverse order of foreign keys)
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS customers;

-- 3. Customers Table
CREATE TABLE customers (
    customer_id VARCHAR(36) NOT NULL,
    signup_date DATE NOT NULL,
    country VARCHAR(10) NOT NULL,
    channel VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (customer_id),
    INDEX idx_customers_signup (signup_date),
    INDEX idx_customers_channel (channel),
    INDEX idx_customers_country (country)
) ENGINE=InnoDB;

-- 4. Subscriptions Table
CREATE TABLE subscriptions (
    subscription_id VARCHAR(36) NOT NULL,
    customer_id VARCHAR(36) NOT NULL,
    plan VARCHAR(20) NOT NULL,
    monthly_price DECIMAL(10, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    end_reason VARCHAR(30) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (subscription_id),
    CONSTRAINT fk_subscriptions_customer
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_subscriptions_customer (customer_id),
    INDEX idx_subscriptions_dates (start_date, end_date),
    INDEX idx_subscriptions_plan (plan),
    INDEX idx_subscriptions_end_reason (end_reason)
) ENGINE=InnoDB;

-- 5. Invoices Table
CREATE TABLE invoices (
    invoice_id VARCHAR(36) NOT NULL,
    customer_id VARCHAR(36) NOT NULL,
    subscription_id VARCHAR(36) NOT NULL,
    invoice_date DATE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    discount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (invoice_id),
    CONSTRAINT fk_invoices_customer
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_invoices_subscription
        FOREIGN KEY (subscription_id) REFERENCES subscriptions (subscription_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_invoices_date (invoice_date),
    INDEX idx_invoices_status (status),
    INDEX idx_invoices_cust_date (customer_id, invoice_date)
) ENGINE=InnoDB;

-- ==============================================================================
-- DATA INGESTION INSTRUCTIONS (MySQL 8.0+)
--
-- Replace '/path/to/data/' with your actual local file directory path.
-- Note: If running on Windows, use forward slashes (e.g. 'C:/my_project/data/customers.csv')
-- Ensure MySQL server variable local_infile is enabled:
--   SET GLOBAL local_infile = 1;
-- Run from mysql client using: mysql --local-infile=1 -u <user> -p
-- ==============================================================================

/*
LOAD DATA LOCAL INFILE '/path/to/data/customers.csv'
INTO TABLE customers
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(customer_id, signup_date, country, channel);

LOAD DATA LOCAL INFILE '/path/to/data/subscriptions.csv'
INTO TABLE subscriptions
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(subscription_id, customer_id, plan, monthly_price, start_date, @v_end_date, @v_end_reason)
SET 
    end_date = NULLIF(@v_end_date, ''),
    end_reason = NULLIF(@v_end_reason, '');

LOAD DATA LOCAL INFILE '/path/to/data/invoices.csv'
INTO TABLE invoices
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(invoice_id, customer_id, subscription_id, invoice_date, amount, discount, status);
*/
