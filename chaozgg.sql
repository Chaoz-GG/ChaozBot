-- phpMyAdmin SQL Dump
-- version 5.1.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Sep 24, 2022 at 09:11 AM
-- Server version: 10.4.18-MariaDB
-- PHP Version: 8.0.3

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `chaozgg`
--

-- --------------------------------------------------------

--
-- Table structure for table `authentication`
--

CREATE TABLE `authentication` (
  `USER_ID` bigint(25) NOT NULL,
  `TOKEN` varchar(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `faceit_stats`
--

CREATE TABLE `faceit_stats` (
  `STEAM_ID` bigint(25) NOT NULL,
  `RANK` int(2) DEFAULT NULL,
  `ELO` int(5) DEFAULT NULL,
  `KPD` float DEFAULT NULL,
  `RATING` float DEFAULT NULL,
  `WIN_RATE` varchar(10) DEFAULT NULL,
  `HS` varchar(10) DEFAULT NULL,
  `MATCHES` int(6) DEFAULT NULL,
  `MOST_PLAYED_MAP` varchar(25) DEFAULT NULL,
  `MOST_SUCCESSFUL_MAP` varchar(25) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `mm_stats`
--

CREATE TABLE `mm_stats` (
  `STEAM_ID` bigint(25) NOT NULL,
  `RANK` varchar(30) NOT NULL,
  `KPD` float NOT NULL,
  `RATING` float NOT NULL,
  `CLUTCH` varchar(10) NOT NULL,
  `BEST_WEAPON` varchar(10) NOT NULL,
  `WIN_RATE` varchar(10) NOT NULL,
  `HS` varchar(10) NOT NULL,
  `ADR` int(3) NOT NULL,
  `ENTRY_SUCCESS` varchar(10) NOT NULL,
  `MOST_PLAYED_MAP` varchar(25) NOT NULL,
  `MOST_SUCCESSFUL_MAP` varchar(25) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `teams`
--

CREATE TABLE `teams` (
  `TEAM_ID` varchar(10) NOT NULL,
  `GAMES` varchar(500) NOT NULL,
  `ACTIVE_GAME` varchar(50) NOT NULL,
  `NAME` varchar(50) NOT NULL,
  `DESCRIPTION` varchar(300) DEFAULT NULL,
  `ORG_NAME` varchar(50) DEFAULT NULL,
  `ABBREVIATION` varchar(5) NOT NULL,
  `REGION` varchar(100) DEFAULT NULL,
  `MESSAGE_ID` bigint(25) DEFAULT NULL,
  `CAPTAIN_STEAM_ID` bigint(25) NOT NULL,
  `CAPTAIN_DISCORD_ID` bigint(25) NOT NULL,
  `MEMBERS_STEAM_IDS` varchar(500) DEFAULT NULL,
  `MEMBERS_DISCORD_IDS` varchar(500) DEFAULT NULL,
  `SUBSTITUTES_STEAM_IDS` varchar(100) DEFAULT NULL,
  `SUBSTITUTES_DISCORD_IDS` varchar(100) DEFAULT NULL,
  `REQUESTED_MEMBERS` varchar(500) DEFAULT NULL,
  `REQUESTED_SUBSTITUTES` varchar(500) DEFAULT NULL,
  `BLACKLIST` varchar(500) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `USER_ID` bigint(25) NOT NULL,
  `STEAM_ID` bigint(25) NOT NULL,
  `BIO` text DEFAULT NULL,
  `COUNTRY` varchar(25) DEFAULT NULL,
  `REGION` varchar(100) DEFAULT NULL,
  `HOURS` int(10) DEFAULT NULL,
  `BIRTHDAY` date DEFAULT NULL,
  `TIMEZONE` varchar(64) NOT NULL DEFAULT 'UTC',
  `FAVORITE_GAMES` varchar(500) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `users_archive`
--

CREATE TABLE `users_archive` (
  `USER_ID` bigint(25) NOT NULL,
  `STEAM_ID` bigint(25) NOT NULL,
  `BIO` text DEFAULT NULL,
  `COUNTRY` varchar(25) DEFAULT NULL,
  `REGION` varchar(100) DEFAULT NULL,
  `HOURS` int(10) DEFAULT NULL,
  `BIRTHDAY` date DEFAULT NULL,
  `TIMEZONE` varchar(64) NOT NULL DEFAULT 'UTC',
  `FAVORITE_GAMES` varchar(500) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `authentication`
--
ALTER TABLE `authentication`
  ADD PRIMARY KEY (`USER_ID`);

--
-- Indexes for table `faceit_stats`
--
ALTER TABLE `faceit_stats`
  ADD PRIMARY KEY (`STEAM_ID`);

--
-- Indexes for table `mm_stats`
--
ALTER TABLE `mm_stats`
  ADD PRIMARY KEY (`STEAM_ID`);

--
-- Indexes for table `teams`
--
ALTER TABLE `teams`
  ADD PRIMARY KEY (`TEAM_ID`),
  ADD UNIQUE KEY `TEAM_ID` (`TEAM_ID`),
  ADD UNIQUE KEY `ABBREVIATION` (`ABBREVIATION`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`USER_ID`);

--
-- Indexes for table `users_archive`
--
ALTER TABLE `users_archive`
  ADD PRIMARY KEY (`USER_ID`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
