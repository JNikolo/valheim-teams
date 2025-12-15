from typing import BinaryIO
from fastapi import HTTPException, UploadFile
from valheim_save_tools_py import ValheimSaveTools


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
            HTTPException: If file parsing fails
        """
        try:
            parsed_data = self.parser.to_json(file, input_file_type=".db")
            if not parsed_data:
                raise HTTPException(
                    status_code=422,
                    detail="Failed to parse .db file or file is empty"
                )
            return parsed_data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid .db file format: {str(e)}"
            )

    def parse_fwl_file(self, file: BinaryIO) -> dict:
        """
        Parse a Valheim .fwl world metadata file and return JSON data.
        
        Args:
            file: Binary file object containing .fwl data
            
        Returns:
            Dictionary containing parsed world metadata
            
        Raises:
            HTTPException: If file parsing fails
        """
        try:
            parsed_data = self.parser.to_json(file, input_file_type=".fwl")
            if not parsed_data:
                raise HTTPException(
                    status_code=422,
                    detail="Failed to parse .fwl file or file is empty"
                )
            return parsed_data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid .fwl file format: {str(e)}"
            )


# Create a singleton instance
valheim_parser = ValheimParserService(verbose=True)
