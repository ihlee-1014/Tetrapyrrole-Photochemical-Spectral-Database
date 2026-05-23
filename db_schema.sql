/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.4.11-MariaDB, for Linux (x86_64)
--
-- Host: bioed-new.bu.edu    Database: Team15
-- ------------------------------------------------------
-- Server version	11.4.11-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `absorption_spectrum`
--

DROP TABLE IF EXISTS `absorption_spectrum`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `absorption_spectrum` (
  `absorption_id` int(11) NOT NULL AUTO_INCREMENT,
  `compound_id` int(11) NOT NULL,
  `file_name` varchar(255) NOT NULL,
  `file_path` varchar(255) DEFAULT NULL,
  `solvent` varchar(50) NOT NULL DEFAULT 'toluene',
  `absorption_lambda_max_nm` decimal(6,2) NOT NULL,
  `molar_absorption_coefficient` int(11) DEFAULT NULL,
  `instrument` varchar(100) DEFAULT NULL,
  `measurement_year` year(4) DEFAULT NULL,
  `reference_code` varchar(50) DEFAULT NULL,
  `investigator` varchar(100) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`absorption_id`),
  KEY `idx_abs_compound` (`compound_id`),
  KEY `idx_abs_lambda` (`absorption_lambda_max_nm`),
  KEY `idx_abs_solvent` (`solvent`),
  KEY `idx_abs_compound_solvent` (`compound_id`,`solvent`)
) ENGINE=InnoDB AUTO_INCREMENT=580 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `compound`
--

DROP TABLE IF EXISTS `compound`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `compound` (
  `compound_id` int(11) NOT NULL,
  `compound_name` varchar(255) NOT NULL,
  `core_metal` varchar(20) DEFAULT NULL,
  `lab_code` varchar(50) DEFAULT NULL,
  `structure_file` varchar(255) DEFAULT NULL,
  `structure_image` varchar(255) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  PRIMARY KEY (`compound_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fluorescence_spectrum`
--

DROP TABLE IF EXISTS `fluorescence_spectrum`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `fluorescence_spectrum` (
  `fluorescence_id` int(11) NOT NULL AUTO_INCREMENT,
  `compound_id` int(11) NOT NULL,
  `solvent` varchar(50) NOT NULL,
  `emission_lambda_max_nm` decimal(6,2) DEFAULT NULL,
  `quantum_yield` varchar(50) DEFAULT NULL,
  `measurement_instrument` varchar(100) DEFAULT NULL,
  `measurement_year` year(4) DEFAULT NULL,
  `reference_code` varchar(50) DEFAULT NULL,
  `investigator` varchar(50) DEFAULT NULL,
  `ems_file_name` varchar(255) NOT NULL,
  `ems_file_path` varchar(255) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`fluorescence_id`),
  KEY `idx_fluor_compound` (`compound_id`),
  KEY `idx_fluor_lambda` (`emission_lambda_max_nm`),
  KEY `idx_fluor_solvent` (`solvent`),
  KEY `idx_fluor_compound_solvent` (`compound_id`,`solvent`),
  CONSTRAINT `fk_fluorescence_compound` FOREIGN KEY (`compound_id`) REFERENCES `compound` (`compound_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=450 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2026-05-22 20:24:11
