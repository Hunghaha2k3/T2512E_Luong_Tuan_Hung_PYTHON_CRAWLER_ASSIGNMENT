-- =====================================================================
-- Chương trình tổng hợp tin tức đa nguồn - Cấu trúc CSDL + dữ liệu mẫu
-- Import vào MySQL/MariaDB (UTF-8): có thể chạy lại nhiều lần, không nhân đôi dữ liệu mẫu.
-- =====================================================================
CREATE DATABASE IF NOT EXISTS dynamic_crawler_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE dynamic_crawler_db;

-- 1. Bảng Chuyên mục
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL DEFAULT NULL
) ENGINE=InnoDB;

-- 2. Bảng Nguồn (cấu hình selector được lưu để tham khảo; mỗi nguồn có class crawler riêng trong thư mục services)
CREATE TABLE IF NOT EXISTS sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    domain VARCHAR(100) NOT NULL,
    path VARCHAR(255) NOT NULL,
    category_id INT NOT NULL,
    description TEXT,
    link_selector VARCHAR(255) DEFAULT NULL,
    title_selector VARCHAR(255) DEFAULT NULL,
    description_selector VARCHAR(255) DEFAULT NULL,
    content_selector VARCHAR(255) DEFAULT NULL,
    image_selector VARCHAR(255) DEFAULT NULL,
    author_selector VARCHAR(255) DEFAULT NULL,
    comment_selector VARCHAR(255) DEFAULT NULL,
    remove_selector VARCHAR(255) DEFAULT NULL,
    status ENUM('active', 'deactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL DEFAULT NULL,
    created_by INT DEFAULT NULL,
    updated_by INT DEFAULT NULL,
    deleted_by INT DEFAULT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 3. Bảng Tin tức (bài viết đã cào)
CREATE TABLE IF NOT EXISTS articles (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    source_id INT NOT NULL,
    category_id INT NOT NULL,
    url VARCHAR(500) NOT NULL,
    alias VARCHAR(255) DEFAULT NULL,
    slug VARCHAR(255) NOT NULL,
    title VARCHAR(255) DEFAULT NULL,
    summary TEXT DEFAULT NULL,
    content LONGTEXT DEFAULT NULL,
    author VARCHAR(100) DEFAULT NULL,
    status ENUM('pending', 'completed', 'deleted') DEFAULT 'pending',
    source_published_at DATETIME DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL DEFAULT NULL,
    created_by INT DEFAULT NULL,
    updated_by INT DEFAULT NULL,
    deleted_by INT DEFAULT NULL,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE RESTRICT,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    UNIQUE KEY unique_url (url)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Dữ liệu mẫu: chỉ thêm khi bảng còn trống (chạy lại file không bị nhân đôi)
-- ---------------------------------------------------------------------
INSERT INTO categories (name, description)
SELECT t.name, t.description FROM (
    SELECT 'Tin tức tổng hợp' AS name, 'Tin tổng hợp từ các nguồn' AS description
    UNION ALL SELECT 'Thể thao', 'Tin thể thao'
    UNION ALL SELECT 'Đời sống', 'Tin đời sống'
) AS t
WHERE NOT EXISTS (SELECT 1 FROM categories);

INSERT INTO sources (name, domain, path, category_id, link_selector, title_selector, description_selector, content_selector, author_selector)
SELECT t.* FROM (
    SELECT 'VnExpress' AS name, 'vnexpress.net' AS domain, '/' AS path, 1 AS category_id,
           'article h3.title-news a' AS link_selector, 'h1.title-detail' AS title_selector,
           'p.description' AS description_selector, 'article.fck_detail p.Normal' AS content_selector,
           'article.fck_detail p.Normal[style*="text-align:right"]' AS author_selector
    UNION ALL SELECT 'Dân trí', 'dantri.com.vn', '/', 1,
           'a[href$=".htm"]', 'h1', 'article h1 ~ h2', 'article h1 ~ div p', 'article h1 ~ div a[href*="/tac-gia/"]'
    UNION ALL SELECT 'Dân Trí (Thể Thao)', 'dantri.com.vn', '/the-thao.htm', 2,
           'a[href$=".htm"]', 'h1', 'article h1 ~ h2', 'article h1 ~ div p', 'article h1 ~ div a[href*="/tac-gia/"]'
    UNION ALL SELECT 'Dân Trí (Đời Sống)', 'dantri.com.vn', '/doi-song.htm', 3,
           'a[href$=".htm"]', 'h1', 'article h1 ~ h2', 'article h1 ~ div p', 'article h1 ~ div a[href*="/tac-gia/"]'
) AS t
WHERE NOT EXISTS (SELECT 1 FROM sources);

-- 4. Bảng Bài viết đã được AI viết lại (bot 3): mỗi bài gốc đúng một bản viết lại
CREATE TABLE IF NOT EXISTS article_rewrite (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    article_id BIGINT NOT NULL,
    title VARCHAR(255) DEFAULT NULL,
    summary TEXT DEFAULT NULL,
    content LONGTEXT DEFAULT NULL,
    status ENUM('completed', 'failed') NOT NULL DEFAULT 'failed',
    error_message VARCHAR(500) DEFAULT NULL,
    attempts INT NOT NULL DEFAULT 0,
    ai_model VARCHAR(100) DEFAULT NULL,
    input_tokens INT DEFAULT NULL,
    output_tokens INT DEFAULT NULL,
    rewritten_at DATETIME DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL DEFAULT NULL,
    UNIQUE KEY unique_rewrite_article (article_id),
    INDEX idx_rewrite_status (status),
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE RESTRICT
) ENGINE=InnoDB;