SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

DROP SCHEMA IF EXISTS `AMON_DATABASE_NAME` ;
CREATE SCHEMA IF NOT EXISTS `AMON_DATABASE_NAME` DEFAULT CHARACTER SET latin1 ;
SHOW WARNINGS;
USE `AMON_DATABASE_NAME` ;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`alertConfig`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`alertConfig` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`alertConfig` (
  `stream` INT NOT NULL ,
  `rev` INT NOT NULL ,
  `validStart` DATETIME NULL DEFAULT NULL ,
  `validStop` DATETIME NULL DEFAULT NULL ,
  `participating` INT NULL DEFAULT NULL COMMENT 'superset of alert.observing' ,
  `p_thresh` FLOAT NULL DEFAULT NULL COMMENT 'universal cut on the pairwise position probability for a clustering analysis' ,
  `N_thresh` VARCHAR(100) NULL DEFAULT NULL COMMENT 'the number thresholds for each observatory' ,
  `deltaT` FLOAT NULL ,
  `cluster_method` VARCHAR(100) NULL ,
  `sens_thresh` VARCHAR(100) NULL ,
  `skymap_val1Desc` VARCHAR(100) NULL DEFAULT NULL ,
  `skymap_val2Desc` VARCHAR(100) NULL DEFAULT NULL ,
  `skymap_val3Desc` VARCHAR(100) NULL DEFAULT NULL ,
  `bufferT` FLOAT NULL ,
  `R_thresh` FLOAT NULL ,
  `cluster_thresh` FLOAT NULL ,
  PRIMARY KEY (`stream`, `rev`) )
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`alert`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`alert` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`alert` (
  `alertConfig_stream` INT NOT NULL ,
  `id` INT NOT NULL ,
  `rev` TINYINT NOT NULL COMMENT 'Revision, 0 preliminary, 1, 2 and so on for updates.' ,
  `time` TIMESTAMP NULL DEFAULT NULL COMMENT 'Time of the alert' ,
  `time_msec` INT NULL ,
  `Dec` FLOAT NULL DEFAULT NULL COMMENT 'Declination ' ,
  `RA` FLOAT NULL DEFAULT NULL COMMENT 'Right ascension' ,
  `sigmaR` FLOAT NULL DEFAULT NULL ,
  `nevents` INT NULL DEFAULT NULL ,
  `deltaT` FLOAT NULL DEFAULT NULL COMMENT 'Time window for events' ,
  `sigmaT` FLOAT NULL ,
  `false_pos` FLOAT NULL DEFAULT NULL COMMENT 'False Alarm Rate density' ,
  `observing` INT NULL DEFAULT NULL COMMENT 'observatories observing' ,
  `trigger` INT NULL DEFAULT NULL COMMENT 'coincidence (2 and more), 0 not reporting, \\\\nsum from 0 to n-1 a_k2^k to get coincidence\\\\nassign each experiment a number' ,
  `type` SET('observation', 'prediction', 'utility', 'test') NULL DEFAULT NULL ,
  `pvalue` FLOAT NULL ,
  `skymap` TINYINT(1) NULL ,
  `alertConfig_rev` INT NOT NULL ,
  PRIMARY KEY (`alertConfig_stream`, `id`, `rev`) ,
  INDEX `fk_alert_alertConfig1_idx` (`alertConfig_stream` ASC, `alertConfig_rev` ASC) ,
  CONSTRAINT `fk_alert_alertConfig1`
    FOREIGN KEY (`alertConfig_stream` , `alertConfig_rev` )
    REFERENCES `AMON_DATABASE_NAME`.`alertConfig` (`stream` , `rev` )
    ON DELETE NO ACTION
    ON UPDATE CASCADE)
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`eventStreamConfig`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`eventStreamConfig` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`eventStreamConfig` (
  `stream` INT NOT NULL ,
  `rev` INT NOT NULL ,
  `validStart` DATETIME NULL DEFAULT NULL ,
  `validStop` DATETIME NULL DEFAULT NULL ,
  `observ_name` VARCHAR(100) NULL DEFAULT NULL ,
  `astro_coord_system` VARCHAR(100) NULL ,
  `obs_coord_system` VARCHAR(100) NULL COMMENT 'Earth-centred or observatory centred coordinate system (eg. UTC-ICRS-TOP.)' ,
  `point_type` VARCHAR(100) NULL DEFAULT NULL COMMENT '0 for long/lat,\\\\n1 for zenith azimuth,\\\\n2 for Dec/RA,\\\\netc.' ,
  `point` VARCHAR(100) NULL DEFAULT NULL COMMENT 'pointing file' ,
  `psf_paramDesc1` VARCHAR(100) NULL DEFAULT NULL ,
  `psf_paramDesc2` VARCHAR(100) NULL DEFAULT NULL ,
  `psf_paramDesc3` VARCHAR(100) NULL DEFAULT NULL ,
  `psf_type` VARCHAR(100) NULL ,
  `psf` VARCHAR(100) NULL DEFAULT NULL ,
  `skymap_val1Desc` VARCHAR(100) NULL DEFAULT NULL ,
  `skymap_val2Desc` VARCHAR(100) NULL DEFAULT NULL ,
  `skymap_val3Desc` VARCHAR(100) NULL DEFAULT NULL ,
  `sensitivity_type` SET('', 'function', 'constant', 'tabulated') NULL ,
  `sensitivity` VARCHAR(100) NULL ,
  `fov_type` SET('circle', 'tabulated') NULL ,
  `fov` VARCHAR(100) NULL ,
  `ephemeris` VARCHAR(100) NULL ,
  `bckgr_type` SET('constant','function', 'tabulated') NULL ,
  `bckgr` VARCHAR(100) NULL ,
  `magn_rigidity` VARCHAR(100) NULL ,
  PRIMARY KEY (`stream`, `rev`) )
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`event`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`event` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`event` (
  `eventStreamConfig_stream` INT NOT NULL ,
  `id` BIGINT NOT NULL COMMENT 'stream id number, set unsigned' ,
  `rev` SMALLINT NOT NULL COMMENT 'revision number, \\\\nTINY INTEGER (set unsigned to go to  fro 0-255)' ,
  `time` DATETIME NULL DEFAULT NULL ,
  `time_msec` INT NULL ,
  `Dec` FLOAT NULL DEFAULT NULL COMMENT 'Declination of the source' ,
  `RA` FLOAT NULL DEFAULT NULL COMMENT 'right ascension of the source\\\\n' ,
  `sigmaR` FLOAT NULL COMMENT 'error2Radius' ,
  `nevents` INT NULL DEFAULT NULL COMMENT 'number of events \\\\nreceived in the event stream from a given experiment. ' ,
  `deltaT` FLOAT NULL DEFAULT NULL COMMENT 'Time window containing individual events ' ,
  `sigmaT` FLOAT NULL ,
  `false_pos` FLOAT NULL DEFAULT NULL COMMENT 'false alarm rate per solid angle' ,
  `pvalue` FLOAT NULL ,
  `type` SET('observation', 'prediction', 'utility', 'test', 'sim') NULL DEFAULT NULL ,
  `point_RA` FLOAT NULL DEFAULT NULL ,
  `point_Dec` FLOAT NULL DEFAULT NULL ,
  `longitude` FLOAT NULL ,
  `latitude` FLOAT NULL ,
  `elevation` FLOAT NULL ,
  `psf_type` SET('skymap','fisher', 'king','kent') NULL COMMENT 'binary to see whether to look for the skimp table or not' ,
  `eventStreamConfig_rev` INT NOT NULL ,
  PRIMARY KEY (`eventStreamConfig_stream`, `id`, `rev`) ,
  INDEX `fk_event_eventStreamConfig1_idx` (`eventStreamConfig_stream` ASC, `eventStreamConfig_rev` ASC) ,
  CONSTRAINT `fk_event_eventStreamConfig1`
    FOREIGN KEY (`eventStreamConfig_stream` , `eventStreamConfig_rev` )
    REFERENCES `AMON_DATABASE_NAME`.`eventStreamConfig` (`stream` , `rev` )
    ON DELETE NO ACTION
    ON UPDATE CASCADE)
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`skyMapEvent`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`skyMapEvent` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`skyMapEvent` (
  `location` VARCHAR(256) NOT NULL COMMENT 'path to map' ,
  `event_eventStreamConfig_stream` INT NOT NULL ,
  `event_id` BIGINT NOT NULL ,
  `event_rev` SMALLINT NOT NULL ,
  PRIMARY KEY (`location`, `event_eventStreamConfig_stream`, `event_id`, `event_rev`) ,
  INDEX `fk_skyMapEvent_event1_idx` (`event_eventStreamConfig_stream` ASC, `event_id` ASC, `event_rev` ASC) ,
  CONSTRAINT `fk_skyMapEvent_event1`
    FOREIGN KEY (`event_eventStreamConfig_stream` , `event_id` , `event_rev` )
    REFERENCES `AMON_DATABASE_NAME`.`event` (`eventStreamConfig_stream` , `id` , `rev` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`skyMapAlert`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`skyMapAlert` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`skyMapAlert` (
  `location` VARCHAR(256) NOT NULL COMMENT 'path to map' ,
  `alert_alertConfig_stream` INT NOT NULL ,
  `alert_id` INT NOT NULL ,
  `alert_rev` TINYINT NOT NULL ,
  PRIMARY KEY (`location`, `alert_alertConfig_stream`, `alert_id`, `alert_rev`) ,
  INDEX `fk_skyMapAlert_alert1_idx` (`alert_alertConfig_stream` ASC, `alert_id` ASC, `alert_rev` ASC) ,
  CONSTRAINT `fk_skyMapAlert_alert1`
    FOREIGN KEY (`alert_alertConfig_stream` , `alert_id` , `alert_rev` )
    REFERENCES `AMON_DATABASE_NAME`.`alert` (`alertConfig_stream` , `id` , `rev` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`messenger`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`messenger` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`messenger` (
  `id` INT NOT NULL ,
  `messenger_type` CHAR(10) NULL ,
  PRIMARY KEY (`id`) )
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`source`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`source` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`source` (
  `id` INT NOT NULL ,
  `source_name` VARCHAR(45) NULL ,
  PRIMARY KEY (`id`) )
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`sourceModel`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`sourceModel` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`sourceModel` (
  `id` INT NOT NULL ,
  `active` TINYINT(1) NULL ,
  `sp_index1` FLOAT NULL ,
  `sp_index2` FLOAT NULL ,
  `sp_threshold` FLOAT NULL ,
  `sp_norm1` FLOAT NULL ,
  `sp_norm2` FLOAT NULL ,
  `sp_break` FLOAT NULL ,
  `messenger_id` INT NOT NULL ,
  `source_id` INT NOT NULL ,
  PRIMARY KEY (`id`, `messenger_id`, `source_id`) ,
  INDEX `fk_sourceModel_messenger1_idx` (`messenger_id` ASC) ,
  INDEX `fk_sourceModel_source1_idx` (`source_id` ASC) ,
  CONSTRAINT `fk_sourceModel_messenger1`
    FOREIGN KEY (`messenger_id` )
    REFERENCES `AMON_DATABASE_NAME`.`messenger` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_sourceModel_source1`
    FOREIGN KEY (`source_id` )
    REFERENCES `AMON_DATABASE_NAME`.`source` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`eventModel`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`eventModel` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`eventModel` (
  `significance` FLOAT NULL DEFAULT NULL ,
  `model_yield` FLOAT NULL DEFAULT NULL ,
  `eventStreamConfig_stream` INT NOT NULL ,
  `eventStreamConfig_rev` INT NOT NULL ,
  `sourceModel_id` INT NOT NULL ,
  `sourceModel_messenger_id` INT NOT NULL ,
  `sourceModel_source_id` INT NOT NULL ,
  `alert_alertConfig_stream` INT NOT NULL ,
  `alert_id` INT NOT NULL ,
  `alert_rev` TINYINT NOT NULL ,
  PRIMARY KEY (`eventStreamConfig_stream`, `eventStreamConfig_rev`, `sourceModel_id`, `sourceModel_messenger_id`, `sourceModel_source_id`, `alert_alertConfig_stream`, `alert_id`, `alert_rev`) ,
  INDEX `fk_eventModel_eventStreamConfig1_idx` (`eventStreamConfig_stream` ASC, `eventStreamConfig_rev` ASC) ,
  INDEX `fk_eventModel_sourceModel1_idx` (`sourceModel_id` ASC, `sourceModel_messenger_id` ASC) ,
  INDEX `fk_eventModel_alert1_idx` (`alert_alertConfig_stream` ASC, `alert_id` ASC, `alert_rev` ASC) ,
  CONSTRAINT `fk_eventModel_eventStreamConfig1`
    FOREIGN KEY (`eventStreamConfig_stream` , `eventStreamConfig_rev` )
    REFERENCES `AMON_DATABASE_NAME`.`eventStreamConfig` (`stream` , `rev` )
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_eventModel_sourceModel1`
    FOREIGN KEY (`sourceModel_id` , `sourceModel_messenger_id` )
    REFERENCES `AMON_DATABASE_NAME`.`sourceModel` (`id` , `messenger_id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_eventModel_alert1`
    FOREIGN KEY (`alert_alertConfig_stream` , `alert_id` , `alert_rev` )
    REFERENCES `AMON_DATABASE_NAME`.`alert` (`alertConfig_stream` , `id` , `rev` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`stream`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`stream` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`stream` (
  `id` INT NOT NULL ,
  `stream_name` VARCHAR(45) NULL ,
  PRIMARY KEY (`id`) )
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`analysisConfig`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`analysisConfig` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`analysisConfig` (
  `stream_id` INT NOT NULL ,
  `rev` TINYINT NOT NULL ,
  `stream_merge_method` SET('setme') NULL ,
  `author` CHAR(100) NULL ,
  `author_contact` CHAR(100) NULL ,
  `deltaT` FLOAT NULL ,
  `select_type` SET('likelihood') NULL ,
  `select_value` FLOAT NULL ,
  `prior1_type` SET('galactic_plane') NULL ,
  `prior1` CHAR(100) NULL ,
  `prior2_type` SET('setme') NULL ,
  `prior2` CHAR(100) NULL ,
  `prior3_type` SET('setme') NULL ,
  `prior3` CHAR(100) NULL ,
  `comments` VARCHAR(200) NULL ,
  PRIMARY KEY (`stream_id`, `rev`) ,
  INDEX `fk_alertConfig_stream1_idx` (`stream_id` ASC) ,
  CONSTRAINT `fk_alertConfig_stream1`
    FOREIGN KEY (`stream_id` )
    REFERENCES `AMON_DATABASE_NAME`.`stream` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`analysis`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`analysis` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`analysis` (
  `alertTime` TIMESTAMP NULL ,
  `significance` FLOAT NULL DEFAULT NULL ,
  `analysisConfig_stream_id` INT NOT NULL ,
  `analysisConfig_rev` TINYINT NOT NULL ,
  `alert_alertConfig_stream` INT NOT NULL ,
  `alert_id` INT NOT NULL ,
  `alert_rev` TINYINT NOT NULL ,
  PRIMARY KEY (`analysisConfig_stream_id`, `analysisConfig_rev`, `alert_alertConfig_stream`, `alert_id`, `alert_rev`) ,
  INDEX `fk_analysis_analysisConfig1_idx` (`analysisConfig_stream_id` ASC, `analysisConfig_rev` ASC) ,
  INDEX `fk_analysis_alert1_idx` (`alert_alertConfig_stream` ASC, `alert_id` ASC, `alert_rev` ASC) ,
  CONSTRAINT `fk_analysis_analysisConfig1`
    FOREIGN KEY (`analysisConfig_stream_id` , `analysisConfig_rev` )
    REFERENCES `AMON_DATABASE_NAME`.`analysisConfig` (`stream_id` , `rev` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_analysis_alert1`
    FOREIGN KEY (`alert_alertConfig_stream` , `alert_id` , `alert_rev` )
    REFERENCES `AMON_DATABASE_NAME`.`alert` (`alertConfig_stream` , `id` , `rev` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`recipient`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`recipient` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`recipient` (
  `id` INT NOT NULL ,
  `name` VARCHAR(80) NULL ,
  `address` VARCHAR(100) NULL ,
  `transmission_format` VARCHAR(45) NULL COMMENT 'transmission format' ,
  PRIMARY KEY (`id`) )
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`distribution`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`distribution` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`distribution` (
  `ranking` FLOAT NULL COMMENT 'rank of the alert for a specific recipient.' ,
  `transmited` TIMESTAMP NULL ,
  `received` TIMESTAMP NULL ,
  `recipient_id` INT NOT NULL ,
  `alert_alertConfig_stream` INT NOT NULL ,
  `alert_id` INT NOT NULL ,
  `alert_rev` TINYINT NOT NULL ,
  PRIMARY KEY (`recipient_id`, `alert_alertConfig_stream`, `alert_id`, `alert_rev`) ,
  INDEX `fk_distribution_recipient1_idx` (`recipient_id` ASC) ,
  INDEX `fk_distribution_alert1_idx` (`alert_alertConfig_stream` ASC, `alert_id` ASC, `alert_rev` ASC) ,
  CONSTRAINT `fk_distribution_recipient1`
    FOREIGN KEY (`recipient_id` )
    REFERENCES `AMON_DATABASE_NAME`.`recipient` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_distribution_alert1`
    FOREIGN KEY (`alert_alertConfig_stream` , `alert_id` , `alert_rev` )
    REFERENCES `AMON_DATABASE_NAME`.`alert` (`alertConfig_stream` , `id` , `rev` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`recipient_has_stream`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`recipient_has_stream` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`recipient_has_stream` (
  `recipient_id` INT NOT NULL ,
  `stream_id` INT NOT NULL ,
  `activation_date` TIMESTAMP NULL ,
  PRIMARY KEY (`recipient_id`, `stream_id`) ,
  INDEX `fk_recipient_has_stream_stream1_idx` (`stream_id` ASC) ,
  INDEX `fk_recipient_has_stream_recipient1_idx` (`recipient_id` ASC) ,
  CONSTRAINT `fk_recipient_has_stream_recipient1`
    FOREIGN KEY (`recipient_id` )
    REFERENCES `AMON_DATABASE_NAME`.`recipient` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_recipient_has_stream_stream1`
    FOREIGN KEY (`stream_id` )
    REFERENCES `AMON_DATABASE_NAME`.`stream` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`follow_up`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`follow_up` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`follow_up` (
  `followup_status` SET('completed', 'rejected', 'in progress', 'comenced') NULL ,
  `start_time` TIMESTAMP NULL ,
  `stop_time` TIMESTAMP NULL ,
  `exposure` FLOAT NULL ,
  `url_data` VARCHAR(100) NULL ,
  `candidate_source_discovered` TINYINT(1) NULL ,
  `pvalue_steady` FLOAT NULL ,
  `pvalue_var` FLOAT NULL ,
  `num_of_observation` INT NULL ,
  `int_bright` FLOAT NULL COMMENT 'integrated brighteness' ,
  `first_observation` TIMESTAMP NULL ,
  `last_observation` TIMESTAMP NULL ,
  `source_Dec` FLOAT NULL ,
  `source_RA` FLOAT NULL ,
  `sigma_Dec` FLOAT NULL ,
  `sigma_RA` FLOAT NULL ,
  `distribution_recipient_id` INT NOT NULL ,
  `distribution_alert_alertConfig_stream` INT NOT NULL ,
  `distribution_alert_id` INT NOT NULL ,
  `distribution_alert_rev` TINYINT NOT NULL ,
  PRIMARY KEY (`distribution_recipient_id`, `distribution_alert_alertConfig_stream`, `distribution_alert_id`, `distribution_alert_rev`) ,
  CONSTRAINT `fk_follow_up_distribution1`
    FOREIGN KEY (`distribution_recipient_id` , `distribution_alert_alertConfig_stream` , `distribution_alert_id` , `distribution_alert_rev` )
    REFERENCES `AMON_DATABASE_NAME`.`distribution` (`recipient_id` , `alert_alertConfig_stream` , `alert_id` , `alert_rev` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`analysisConfig_has_sourceModel`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`analysisConfig_has_sourceModel` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`analysisConfig_has_sourceModel` (
  `analysisConfig_stream_id` INT NOT NULL ,
  `analysisConfig_rev` TINYINT NOT NULL ,
  `sourceModel_id` INT NOT NULL ,
  `sourceModel_messenger_id` INT NOT NULL ,
  `sourceModel_source_id` INT NOT NULL ,
  PRIMARY KEY (`analysisConfig_stream_id`, `analysisConfig_rev`, `sourceModel_id`, `sourceModel_messenger_id`, `sourceModel_source_id`) ,
  INDEX `fk_analysisConfig_has_sourceModel_sourceModel1_idx` (`sourceModel_id` ASC, `sourceModel_messenger_id` ASC) ,
  INDEX `fk_analysisConfig_has_sourceModel_analysisConfig1_idx` (`analysisConfig_stream_id` ASC, `analysisConfig_rev` ASC) ,
  CONSTRAINT `fk_analysisConfig_has_sourceModel_analysisConfig1`
    FOREIGN KEY (`analysisConfig_stream_id` , `analysisConfig_rev` )
    REFERENCES `AMON_DATABASE_NAME`.`analysisConfig` (`stream_id` , `rev` )
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_analysisConfig_has_sourceModel_sourceModel1`
    FOREIGN KEY (`sourceModel_id` , `sourceModel_messenger_id` )
    REFERENCES `AMON_DATABASE_NAME`.`sourceModel` (`id` , `messenger_id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`parameter`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`parameter` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`parameter` (
  `name` VARCHAR(50) NOT NULL COMMENT 'Name of the parameter, which could be \"energy\", Error2Radius, Kent_beta, etc. depending what is the event parameter' ,
  `value` DOUBLE NULL ,
  `units` VARCHAR(45) NULL ,
  `event_eventStreamConfig_stream` INT NOT NULL ,
  `event_id` BIGINT NOT NULL ,
  `event_rev` SMALLINT NOT NULL ,
  PRIMARY KEY (`name`, `event_eventStreamConfig_stream`, `event_id`, `event_rev`) ,
  INDEX `fk_parameter_event1_idx` (`event_eventStreamConfig_stream` ASC, `event_id` ASC, `event_rev` ASC) ,
  CONSTRAINT `fk_parameter_event1`
    FOREIGN KEY (`event_eventStreamConfig_stream` , `event_id` , `event_rev` )
    REFERENCES `AMON_DATABASE_NAME`.`event` (`eventStreamConfig_stream` , `id` , `rev` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

SHOW WARNINGS;

-- -----------------------------------------------------
-- Table `AMON_DATABASE_NAME`.`alertLine`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `AMON_DATABASE_NAME`.`alertLine` ;

SHOW WARNINGS;
CREATE  TABLE IF NOT EXISTS `AMON_DATABASE_NAME`.`alertLine` (
  `alert_alertConfig_stream` INT NOT NULL ,
  `alert_id` INT NOT NULL ,
  `alert_rev` TINYINT NOT NULL ,
  `event_eventStreamConfig_stream` INT NOT NULL ,
  `event_id` BIGINT NOT NULL ,
  `event_rev` SMALLINT NOT NULL ,
  PRIMARY KEY (`alert_alertConfig_stream`, `alert_id`, `alert_rev`, `event_eventStreamConfig_stream`, `event_id`, `event_rev`) ,
  INDEX `fk_alert_has_event_event1_idx` (`event_eventStreamConfig_stream` ASC, `event_id` ASC, `event_rev` ASC) ,
  INDEX `fk_alert_has_event_alert1_idx` (`alert_alertConfig_stream` ASC, `alert_id` ASC, `alert_rev` ASC) ,
  CONSTRAINT `fk_alert_has_event_alert1`
    FOREIGN KEY (`alert_alertConfig_stream` , `alert_id` , `alert_rev` )
    REFERENCES `AMON_DATABASE_NAME`.`alert` (`alertConfig_stream` , `id` , `rev` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_alert_has_event_event1`
    FOREIGN KEY (`event_eventStreamConfig_stream` , `event_id` , `event_rev` )
    REFERENCES `AMON_DATABASE_NAME`.`event` (`eventStreamConfig_stream` , `id` , `rev` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

SHOW WARNINGS;
USE `AMON_DATABASE_NAME` ;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
