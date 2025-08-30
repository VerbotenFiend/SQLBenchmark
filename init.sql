CREATE DATABASE IF NOT EXISTS moviesdb;
USE moviesdb;

-- Registi
CREATE TABLE IF NOT EXISTS regista (
  idR INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(255) NOT NULL UNIQUE,
  eta INT NOT NULL
);

-- Piattaforme
CREATE TABLE IF NOT EXISTS piattaforma (
  idP INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(100) NOT NULL UNIQUE
);

-- Film 
CREATE TABLE IF NOT EXISTS movies (
  idF INT AUTO_INCREMENT PRIMARY KEY,
  titolo VARCHAR(255) NOT NULL UNIQUE,
  idR INT NOT NULL,
  anno INT NOT NULL,
  genere VARCHAR(100) NOT NULL,
  CONSTRAINT fk_movies_regista FOREIGN KEY (idR) REFERENCES regista(idR)
  ON DELETE CASCADE
);

-- Disponibilità su piattaforme 
CREATE TABLE IF NOT EXISTS dove_vederlo (
  idF INT PRIMARY KEY,
  idP1 INT NULL,
  idP2 INT NULL,
  CONSTRAINT fk_dv_film FOREIGN KEY (idF) REFERENCES movies(idF) ON DELETE CASCADE,
  CONSTRAINT fk_dv_p1 FOREIGN KEY (idP1) REFERENCES piattaforma(idP),
  CONSTRAINT fk_dv_p2 FOREIGN KEY (idP2) REFERENCES piattaforma(idP),
  CONSTRAINT chk_two_distinct CHECK (idP1 IS NULL OR idP2 IS NULL OR idP1 <> idP2)
);

-- Indici utili 
CREATE INDEX idx_movies_anno ON movies(anno);
CREATE INDEX idx_regista_eta ON regista(eta);
CREATE INDEX idx_dv_p1 ON dove_vederlo(idP1);
CREATE INDEX idx_dv_p2 ON dove_vederlo(idP2);
