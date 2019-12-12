import unigdb.config
# import unigdb.proc

UNIGDB_PROMPT = "unigdb\u27a4  "
UNIGDB_PROMPT_ON = "\001\033[1;32m\002{0:s}\001\033[0m\002".format(UNIGDB_PROMPT)
UNIGDB_PROMPT_OFF = "\001\033[1;31m\002{0:s}\001\033[0m\002".format(UNIGDB_PROMPT)


def set_prompt(current_prompt):
    """PWNunigdb custom prompt function."""
    if unigdb.config.get("self.readline_compat") is True:
        return UNIGDB_PROMPT
    if unigdb.config.get("self.disable_color") is True:
        return UNIGDB_PROMPT
    # if unigdb.proc.alive:
    #     return UNIGDB_PROMPT_ON
    return UNIGDB_PROMPT_OFF
