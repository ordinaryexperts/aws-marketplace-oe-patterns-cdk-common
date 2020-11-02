from aws_cdk import core

class Util:

    # utility function to parse the unique id from the stack id for                                                 
    # shorter resource names using cloudformation functions
    @staticmethod
    def append_stack_uuid(name):
        return core.Fn.join("-", [
            name,
	    core.Fn.select(2, core.Fn.split("/", core.Aws.STACK_ID))
        ])
