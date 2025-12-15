from typing import BinaryIO
from valheim_save_tools_py import ValheimSaveTools
from ..logging_config import get_logger
from ..exceptions import ParsingError

logger = get_logger(__name__)


class ValheimParserService:
    """
    Service for parsing Valheim save files.
    
    Handles the conversion of .db and .fwl binary files into JSON format
    using the valheim-save-tools-py library.
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize the parser service.
        
        Args:
            verbose: Enable verbose logging in the parser
        """
        self.parser = ValheimSaveTools(verbose=verbose)

    def parse_db_file(self, file: BinaryIO) -> dict:
        """
        Parse a Valheim .db save file and return JSON data.
        
        Args:
            file: Binary file object containing .db data
            
        Returns:
            Dictionary containing parsed save data
            
        Raises:
            ParsingError: If file parsing fails
        """
        try:
            logger.debug("Parsing .db file...")
            parsed_data = self.parser.to_json(file, input_file_type=".db")
            if not parsed_data:
                logger.error("Parser returned empty data for .db file")
                raise ParsingError(".db", "File is empty or could not be parsed")
            logger.debug(f".db file parsed successfully, found {len(parsed_data.get('zdoList', []))} ZDOs")
            return parsed_data
        except ParsingError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse .db file: {e}", exc_info=True)
            raise ParsingError(".db", str(e))

    def parse_fwl_file(self, file: BinaryIO) -> dict:
        """
        Parse a Valheim .fwl world metadata file and return JSON data.
        
        Args:
            file: Binary file object containing .fwl data
            
        Returns:
            Dictionary containing parsed world metadata
            
        Raises:
            ParsingError: If file parsing fails
        """
        try:
            logger.debug("Parsing .fwl file...")
            parsed_data = self.parser.to_json(file, input_file_type=".fwl")
            if not parsed_data:
                logger.error("Parser returned empty data for .fwl file")
                raise ParsingError(".fwl", "File is empty or could not be parsed")
            logger.debug(f".fwl file parsed successfully, world: {parsed_data.get('name', 'unknown')}")
            return parsed_data
        except ParsingError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse .fwl file: {e}", exc_info=True)
            raise ParsingError(".fwl", str(e))


# Create a singleton instance
valheim_parser = ValheimParserService(verbose=True)
