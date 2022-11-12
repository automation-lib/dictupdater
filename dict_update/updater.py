"""This library is used to update any nested dict and list object .


How to use :

DictUpdater : Used to map  operation and dictionary update data .

    @param
    operation_mapping :{ dictionary path separated by dot or ->  : {
             {
                "operation": "update/delete/append",
                "key": "versionnumber"
            }
    }}


Example 1:

sample.py

    value_1 = {"metafilesList": [{
        "groupname": "",
        "filetype": "CLI",
        "appversion": "1",
        "version": "1",
        "metafileobjectsList": [{
            "filename": "filename",
            "tempurl": ""}]},
        {
            "groupname": "",
            "filetype": "CLI",
            "appversion": "1",
            "version": "2",
            "metafileobjectsList": [{
                "filename": "filename",
                "tempurl": ""}, {
                "filename": "filename2",
                "tempurl": ""}]}]}

    # Step 1 : Create a operation mapping , All keys are path to update for operation
    # operation : update
    # key : it used for searching dict object in a list
    operation_mapping = {
        "metafilesList": {
            "operation": "update",
            "key": "version"
        },
        "metafilesList->metafileobjectsList": {
            "operation": "update",
            "key": "filename"
        }}

    # Step 2 Create Update value mapping
    update_value = {"metafilesList": [
        {
            "version": "2",
            "metafileobjectsList": [{
                "filename": "filename",
                "tempurl": "new value"}]}]}

    DictUpdater(operation_mapping=operation_mapping).recursive_dict_updater(data=value_1,
                                                                            update_value=update_value)
    print(value_1)

    # For delete and append operation , replace metafilesList->metafileobjectsList , operation : append or delete


TODO: Add key comparison mechanism
TODO: Add logger dump
"""
import logging
from copy import deepcopy


class DictUpdater:
    class Operation:
        UPDATE = "update"
        APPEND = "append"
        DELETE = "delete"

    def __init__(self, operation_mapping=None):

        self._logger = logging.getLogger(__name__)

        if operation_mapping is None:
            operation_mapping = {}
        self.default_operation = {
        }

        for each_key in operation_mapping:
            new_key = each_key.replace("->", ".")
            self.default_operation[new_key] = operation_mapping[each_key]
        # self.default_operation.update(operation_mapping)

    def _recursive_dict_updater(
            self,
            data,
            update_value,
            base_path="",
            separator="->"):
        """It update exiting data with update value ,

        @param data: Dictionary data which need to updated
        @param update_value: Value through which dictionary data get updated .
        @param base_path: It required to check mapping for operation.
        @param separator: It is used to pass custom seperator
        @return:
        """
        self._logger.info(base_path)
        base_path = base_path.strip(separator)
        base_path = base_path.replace(separator, ".")

        if isinstance(update_value, dict):
            for key, each_value in update_value.items():

                # Check if key is not present in data add it
                if not data.get(key):
                    data[key] = each_value
                    continue

                # Update again recursively to validate changes
                data[key] = self._recursive_dict_updater(
                    data=data[key],
                    update_value=each_value,
                    base_path=base_path + separator + str(key))

            # Return the update data dict
            return data

        # if instance is list and contain is dictionary
        if isinstance(update_value, list) and len(
                update_value) > 0:  # and isinstance(update_value[0], dict)

            # Check data dict also have type dict and if contain list is empty
            # then no need to perform operation
            if isinstance(data, list) and len(data) < 0:
                return update_value

            if isinstance(
                    data,
                    list) and len(data) > 0 and not isinstance(
                data[0],
                dict):
                ValueError(
                    f"You try to update not dictionary object : {data} and base path : {base_path}")

            # Check already specified operation define for search
            operation = self.default_operation.get(base_path)

            # If no operation define
            if not operation:
                return update_value

            if operation["operation"] == DictUpdater.Operation.UPDATE:
                search_key = operation.get("key")

                if search_key is None:
                    raise ValueError(
                        "You must provide the search key to update dict object")

                return self._update_operation(
                    base_path, data, search_key, update_value)

            if operation["operation"] == DictUpdater.Operation.APPEND:
                for index, value in enumerate(update_value):
                    data.append(value)

                return data

            if operation["operation"] == DictUpdater.Operation.DELETE:
                for index, value in enumerate(update_value):
                    search_key = operation.get("key")
                    search_value = value.get(search_key)
                    found = False
                    for data_index, data_value in enumerate(data):
                        if search_value == data_value.get(search_key):
                            del data[data_index]
                            found = True

                    if not found:
                        self._logger.warning(
                            f"search key:{search_key} value:{search_key}  not found")

                return data

        # TODO : Implement string replacement algo
        elif isinstance(update_value, list) and len(update_value) > 0 and isinstance(update_value[0], str):
            # Check already specified operation define for search
            pass
        else:
            # Override the list as specified operation not mention
            return update_value

    def _update_operation(self, base_path, data, search_key, update_value):
        # search if it is present else append
        for index, value in enumerate(update_value):
            search_value = value.get(search_key)
            if search_value is None:
                print("search criteria not define so appending as it is")
                data.append(value)
                continue

            replace_value = None
            if "->" in search_value:
                split_result = search_value.split("->")
                search_value = split_result[0]
                replace_value = split_result[-1]

            found = False
            for data_index, data_value in enumerate(data):
                if search_value == data_value.get(search_key):
                    # data[data_index] = value
                    data[data_index] = self._recursive_dict_updater(
                        data=data[data_index], update_value=value, base_path=base_path)

                    if replace_value:
                        data[data_index][search_key] = replace_value

                    found = True

            if not found:
                data.append(value)
        return data

    @staticmethod
    def update(data, update_value, separator="->", operation_mapping=None, data_muted=False):

        if data_muted:
            data = deepcopy(data)

        update_obj = DictUpdater(operation_mapping=operation_mapping)
        return update_obj._recursive_dict_updater(data=data, update_value=update_value, separator=separator)


if __name__ == '__main__':
    value_1 = {"metafilesList": [{
        "groupname": "",
        "filetype": "CLI",
        "appversion": "1",
        "version": "1",
        "metafileobjectsList": [{
            "filename": "filename",
            "tempurl": ""}]},
        {
            "groupname": "",
            "filetype": "CLI",
            "appversion": "1",
            "version": "2",
            "metafileobjectsList": [{
                "filename": "filename",
                "tempurl": ""}, {
                "filename": "filename2",
                "tempurl": ""}]}]}

    # Step 1 : Create a operation mapping , All keys are path to update for operation
    # operation : update
    # key : it used for searching dict object in a list
    operation_mapping_value = {
        "metafilesList": {
            "operation": "update",
            "key": "version"
        },
        "metafilesList->metafileobjectsList": {
            "operation": "update",
            "key": "filename"
        }}

    # Step 2 Create Update value mapping
    update_value_required = {"metafilesList": [
        {
            "version": "2",
            "metafileobjectsList": [{
                "filename": "filename->kunal",
                "tempurl": "new value"}]}]}

    DictUpdater.update(data=value_1, update_value=update_value_required)

    from pprint import pprint

    pprint(value_1)

    # Step 2 Updating the search key (use case 1)
    # filename2 get replace with new demo
    update_value_required = {"metafilesList": [
        {
            "version": "2",
            "metafileobjectsList": [{
                "filename": "filename2->new demo",
                "tempurl": "new value"}]}]}

    DictUpdater.update(
        data=value_1,
        update_value=update_value_required,
        operation_mapping=operation_mapping_value
    )
    from pprint import pprint

    pprint(value_1)

    # For delete and append operation , replace
    # metafilesList->metafileobjectsList , operation : append or delete
