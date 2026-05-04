from modules.biosafety.data.BUA_data_structure import BUAForm, current_bua_state

class BUABatchImport:
    def initiate(self):
        # No specific initialization required
        pass

    def run(self, full_bua_data: str) -> dict:
        """
        Takes the fully extracted JSON from the LLM and completely overwrites 
        the current BUA state.
        """
        # We need to modify the global state object
        global current_bua_state 
        
        try:
            # 1. Parse the LLM's string into a Python dictionary
            data = json.loads(full_bua_data)

            # 2. Validate the entire dictionary against the master Pydantic model.
            # This automatically checks LabIdentity, Strains, and Personnel all at once!
            validated_form = BUAForm(**data)

            # 3. Update the global state with the new validated data
            current_bua_state.lab_identity = validated_form.lab_identity
            current_bua_state.strains = validated_form.strains
            current_bua_state.personnel = validated_form.personnel

            # 4. Return success to the LLM so it knows it can move on to analysis
            return {
                "status": "success",
                "message": "The uploaded BUA document data was successfully validated and saved to the central state. You may now run analysis or render the document.",
                "current_state": current_bua_state.model_dump()
            }

        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Failed to parse JSON. Ensure you are sending a valid JSON string."
            }
        except Exception as e:
            # If any required fields are missing or types are wrong, Pydantic catches it here
            return {
                "status": "error",
                "message": f"Data validation failed: {str(e)}. Please correct the extracted JSON and try again."
            }

# Standard C9 instantiation and export
_instance = BUABatchImport()
_instance.initiate()
bua_batch_import = _instance.run