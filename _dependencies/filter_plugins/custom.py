#!/usr/bin/env python

from ansible.utils.display import Display

display = Display()


# Convert a YAML object (e.g. perhaps converted with dseeley.ansible_vault_pipe.encrypt) containing $ANSIBLE_VAULT to a yaml multiline string beginning "!vault |".  Useful to output vaulted yaml to a file without decrypting.
def to_yaml_vaulted(ansible_obj):
    import yaml, json
    from ansible.template import AnsibleUndefined
    from ansible.utils.unsafe_proxy import AnsibleUnsafeText
    from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode

    # def to_py_native(value):
    #     """Recursively convert Ansible special objects to plain Python types.  Fails when using loading already-vaulted yaml."""
    #     if isinstance(value, (AnsibleUnsafeText, AnsibleUndefined)):
    #         return str(value)  # ← strips unsafe/lazy flag
    #     if isinstance(value, AnsibleVaultEncryptedUnicode):
    #         # Keep vault content as original string — exactly what we want
    #         return value._ciphertext.decode('utf-8') if hasattr(value, '_ciphertext') else str(value)
    #     if isinstance(value, dict):
    #         return {k: to_py_native(v) for k, v in value.items()}
    #     if isinstance(value, (list, tuple)):
    #         return [to_py_native(item) for item in value]
    #     return value
    #
    # clean_obj = to_py_native(ansible_obj)                             # Fails when using loading already-vaulted yaml.

    clean_obj = json.loads(json.dumps(ansible_obj, default=str))      # Works with already-vaulted yaml.  Problem is already-vaulted yaml is unvaulted here.

    # Now we only have safe Python types → no pickling problems
    def str_presenter(dumper, data):
        if isinstance(data, str) and data.startswith('$ANSIBLE_VAULT'):
            return dumper.represent_scalar(u'!vault', data, style='|')
        if isinstance(data, str) and '\n' in data:
            return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar(u'tag:yaml.org,2002:str', data)

    yaml.add_representer(str, str_presenter)
    yaml.representer.SafeRepresenter.add_representer(str, str_presenter)

    # width=4096 prevents unwanted line wrapping
    return yaml.dump(clean_obj, width=4096, allow_unicode=True, encoding='utf-8').decode('utf-8')


class FilterModule(object):
    def filters(self):
        return {'to_yaml_vaulted': to_yaml_vaulted}


# Convert a YAML string with the "!vault" tag to a plain (not-decrypted) yaml Object (without the tag).  Useful for loading vaulted string as encrypted yaml.
def from_yaml_vaulted(yamlstr):
    import yaml

    def vault_constructor(loader, node):
        value = loader.construct_scalar(node)
        return (value)

    yaml.add_constructor(u'!vault', vault_constructor)

    return yaml.load(yamlstr, Loader=yaml.FullLoader)


class FilterModule(object):
    def filters(self):
        return {
            'from_yaml_vaulted': from_yaml_vaulted,
            'to_yaml_vaulted': to_yaml_vaulted
        }
