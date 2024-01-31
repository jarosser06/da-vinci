from typing import Optional

from os import path as pathlib

from aws_cdk import (
    DockerImage,
    Stack as CDKStack,
)

from constructs import Construct


class Stack(CDKStack):
    def __init__(self, app_name: str,
                 deployment_id: str, scope: Construct, stack_name: str,
                 app_base_image: Optional[DockerImage] = None,
                 architecture: Optional[str] = None,
                 library_base_image: Optional[DockerImage] = None,
                 required_stacks: Optional[list] = None):
        """
        Initialize a new Stack object

        Keyword Arguments:
            app_name: Name of the application
            architecture: Architecture to use for the stack
            create_sub_domain: Create a sub domain for the stack (default: None)
            deployment_id: Identifier assigned to the installation
            scope: Parent construct for the stack
            stack_name: Name of the stack
            app_base_image: Base image built for the application (default: None)
            library_base_image: Base image built for the library (default: None)
            required_stacks: List of stacks required by this stack (default: None)

        Example:
            ```
            from da_vinci_cdk.application import Application
            from da_vinci_cdk.stack import Stack

            class MyStack(Stack):
                def __init__(self, app_name: str, architecture: str, deployment_id: str,
                             scope: Construct, stack_name: str):
                    super().__init__(
                        app_name=app_name,
                        architecture=architecture,
                        deployment_id=deployment_id,
                        scope=scope,
                        stack_name=stack_name,
                    )
                    ...

            app = Application(
                app_name='da_vinci',
                deployment_id='da_vinci',
            )

            app.add_uninitialized_stack(MyStack)

            app.synth()
            ```
        """

        self.da_vinci_stack_name = f'{deployment_id}-{stack_name}'

        construct_id = self.da_vinci_stack_name

        super().__init__(scope, construct_id)

        self.app_name = app_name
        self.architecture = architecture
        self.deployment_id = deployment_id

        self.app_base_image = app_base_image
        self.library_base_image = library_base_image
        self.required_stacks = required_stacks or []

    def add_required_stack(self, stack: 'Stack'):
        '''
        Add a required dependency stack to the stack instance

        Keyword Arguments:
            stack: Stack to add as a required stack
        '''
        self.required_stacks.append(stack)

    @staticmethod
    def absolute_dir(from_file: str) -> str:
        '''
        Static method to return the absolute path of a file

        Keyword Arguments:
            from_file: File to return the absolute path of
        '''
        return pathlib.dirname(pathlib.realpath(from_file))