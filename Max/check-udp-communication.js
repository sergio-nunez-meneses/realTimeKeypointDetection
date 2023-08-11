// ============================================================================
//  Globals
// ============================================================================
autowatch = 1;
inlets    = 1;
outlets   = 1;

// ============================================================================
//  Functions
// ============================================================================
function anything() {
	var errors = [];

	var address = messagename;
	if (address.slice(1) !== "connect") {
		errors.push("OSC address pattern must be /connect");
	}

	if (arguments.length === 0) {
		errors.push("OSC argument must not be empty");
	}
	if (arguments.length > 1) {
		errors.push("OSC argument must not have more than 1 element");
	}

	var message = arguments[0];
	if (typeof message !== "string") {
		errors.push("OSC argument must be of type string");
	}

	var re = new RegExp(/\{([^}]+)\}/);
	var params = re.exec(message);
	var response = {};
	var parse;

	if (params === null) {
		errors.push("OSC parsed argument must be of type JSON string");
	}
	else {
		parse = JSON.parse(message);

		if (typeof parse["connected"] !== "boolean") {
			errors.push("OSC parsed value must be of type boolean");
		}
	}

	if (errors.length > 0) {
		for (var i = 0; i < errors.length; i++) {
			post("Error: " + errors[i] + "\n");
		}
		response["errors"] = errors.join(", ");
	}
	else {
		response["connected"] = !parse["connected"] ? true : parse["connected"];
	}

	outlet(0, ["/connect", JSON.stringify(response)]);
}
