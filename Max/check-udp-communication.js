// ============================================================================
//  Globals
// ============================================================================
autowatch = 1;
inlets    = 1;
outlets   = 2;

// ============================================================================
//  Variables
// ============================================================================
var addresses = ["connect"];

// ============================================================================
//  Functions
// ============================================================================
function anything() {
	var address  = messagename.slice(1);
	var errors   = checkMessageFormat(address, arguments);
	var response = {};

	if (errors.length > 0) {
		printErrors(errors);
	}
	else {
		parse  = JSON.parse(arguments[0]);
		errors = [];

		if (address === "connect") {
			if (typeof parse["connected"] !== "boolean") {
				errors.push("OSC parsed value must be of type boolean");
			}

			if (errors.length > 0) {
				response["errors"] = errors.join(", ");
			}
			else {
				response["connected"] = !parse["connected"] ? true : parse["connected"];
			}
			outlet(0, [messagename, JSON.stringify(response)]);
		}
	}
}

function checkMessageFormat(address, data) {
	var errors = [];

	if (addresses.indexOf(address) === -1) {
		errors.push("OSC address pattern must be /connect, /left_hand, or /right_hand");
	}

	if (data.length === 0) {
		errors.push("OSC argument must not be empty");
	}
	if (data.length > 1) {
		errors.push("OSC argument must not have more than 1 element");
	}

	var message = data[0];
	if (typeof message !== "string") {
		errors.push("OSC argument must be of type string");
	}

	var re     = new RegExp(/\{([^}]+)\}/);
	var params = re.exec(message);

	if (params === null) {
		errors.push("OSC parsed argument must be of type JSON string");
	}

	return errors;
}

function printErrors(errors) {
	for (var i = 0; i < errors.length; i++) {
		post("Error: " + errors[i] + "\n");
	}
}
