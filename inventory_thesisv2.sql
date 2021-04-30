-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema inventory_thesis
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema inventory_thesis
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `inventory_thesis` DEFAULT CHARACTER SET utf8 ;
USE `inventory_thesis` ;

-- -----------------------------------------------------
-- Table `inventory_thesis`.`inventory`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `inventory_thesis`.`inventory` (
  `idInventory` INT NOT NULL AUTO_INCREMENT,
  `item_name` VARCHAR(45) NOT NULL,
  `item_description` VARCHAR(125) NOT NULL,
  PRIMARY KEY (`idInventory`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `inventory_thesis`.`returned`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `inventory_thesis`.`returned` (
  `idreturned` INT NOT NULL AUTO_INCREMENT,
  `idInventory` INT NOT NULL,
  `datetime` DATETIME NOT NULL,
  `camera` INT NOT NULL,
  PRIMARY KEY (`idreturned`, `idInventory`),
  INDEX `fk_time_in_inventory_idx` (`idInventory` ASC) VISIBLE,
  CONSTRAINT `fk_time_in_inventory`
    FOREIGN KEY (`idInventory`)
    REFERENCES `inventory_thesis`.`inventory` (`idInventory`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `inventory_thesis`.`borrowed`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `inventory_thesis`.`borrowed` (
  `idborrowed` INT NOT NULL AUTO_INCREMENT,
  `idInventory` INT NOT NULL,
  `datetime` DATETIME NOT NULL,
  `camera` INT NOT NULL,
  PRIMARY KEY (`idborrowed`, `idInventory`),
  INDEX `fk_time_out_inventory1_idx` (`idInventory` ASC) VISIBLE,
  CONSTRAINT `fk_time_out_inventory1`
    FOREIGN KEY (`idInventory`)
    REFERENCES `inventory_thesis`.`inventory` (`idInventory`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `inventory_thesis`.`StockIn`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `inventory_thesis`.`StockIn` (
  `idStockIn` INT NOT NULL,
  `idInventory` INT NOT NULL,
  `dateStockIn` DATETIME NOT NULL,
  `totalStockIn` INT NOT NULL,
  PRIMARY KEY (`idStockIn`, `idInventory`),
  INDEX `fk_StockIn_inventory1_idx` (`idInventory` ASC) VISIBLE,
  CONSTRAINT `fk_StockIn_inventory1`
    FOREIGN KEY (`idInventory`)
    REFERENCES `inventory_thesis`.`inventory` (`idInventory`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
