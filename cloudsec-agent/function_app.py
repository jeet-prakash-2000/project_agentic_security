import azure.functions as func

from services.get_incidents_service import (
    get_incidents_service
)

from services.get_incident_service import (
    get_incident_service
)

from services.generate_summary_service import (
    generate_summary_service
)

from services.get_vm_context_service import (
    get_vm_context_service
)

from services.get_vm_instance_view_service import (
    get_vm_instance_view_service
)

from services.start_vm_service import (
    start_vm_service
)

from services.stop_vm_service import (
    stop_vm_service
)

from services.restart_vm_service import (
    restart_vm_service
)

from services.isolate_vm_service import (
    isolate_vm_service
)

from services.reconnect_vm_service import (
    reconnect_vm_service
)


app = func.FunctionApp(
    http_auth_level=func.AuthLevel.FUNCTION
)


@app.route(
    route="GetSentinelIncidents",
    methods=["POST"]
)
def GetSentinelIncidents(
    req: func.HttpRequest
):
    return get_incidents_service(req)


@app.route(
    route="GetSentinelIncident",
    methods=["POST"]
)
def GetSentinelIncident(
    req: func.HttpRequest
):
    return get_incident_service(req)


@app.route(
    route="GenerateIncidentSummary",
    methods=["POST"]
)
def GenerateIncidentSummary(
    req: func.HttpRequest
):
    return generate_summary_service(req)


@app.route(
    route="GetVMContext",
    methods=["POST"]
)
def GetVMContext(
    req: func.HttpRequest
):
    return get_vm_context_service(req)


@app.route(
    route="GetVMInstanceView",
    methods=["POST"]
)
def GetVMInstanceView(
    req: func.HttpRequest
):
    return get_vm_instance_view_service(req)


@app.route(
    route="StartVM",
    methods=["POST"]
)
def StartVM(
    req: func.HttpRequest
):
    return start_vm_service(req)


@app.route(
    route="StopVM",
    methods=["POST"]
)
def StopVM(
    req: func.HttpRequest
):
    return stop_vm_service(req)


@app.route(
    route="RestartVM",
    methods=["POST"]
)
def RestartVM(
    req: func.HttpRequest
):
    return restart_vm_service(req)


@app.route(
    route="IsolateAzureVM",
    methods=["POST"]
)
def IsolateAzureVM(
    req: func.HttpRequest
):
    return isolate_vm_service(req)


@app.route(
    route="RestoreVMConnectivity",
    methods=["POST"]
)
def RestoreVMConnectivity(
    req: func.HttpRequest
):
    return reconnect_vm_service(req)