// ============================================================================
//  Globals
// ============================================================================
autowatch = 1;
inlets    = 1;
outlets   = 2;

// ============================================================================
//  Variables
// ============================================================================
var addresses  = ["connect", "left_hand", "right_hand"];
var handsExist = {
	"rh": false,
	"lh": false,
}

// ============================================================================
//  Functions
// ============================================================================
function anything() {
	var address  = messagename.slice(1);
	var errors   = checkMessageFormat(address, arguments);
	var response = {};

	if (errors.length > 0) {
		handleErrorMessages(messagename, errors);
	}
	else {
		var parse  = JSON.parse(arguments[0]);
		var errors = checkMessageValue(address, parse);

		if (errors.length > 0) {
			handleErrorMessages(messagename, errors);
		}
		else {
			if (address === "connect") {
				var response = {
					"connected": !parse["connected"] ? true : parse["connected"],
				}
				sendToUdpServer(messagename, response);
			}
			else if (contains(address, "_hand")) {
				var key = getObjKey(parse);

				if (typeof parse[key] === "boolean") {
					var hand         = contains(address, "right") ? "rh" : "lh";
					handsExist[hand] = parse[key];
				}
				else {
					if (handsExist["rh"] || handsExist["lh"]) {
						var v = parse[key];
						outlet(1, [messagename, key, v["i"], v["x"], v["y"], v["z"]]);
					}
				}
			}
		}
	}
}

function checkMessageFormat(address, data) {
	var errors = [];

	if (!contains(addresses, address)) {
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

function checkMessageValue(address, data) {
	var key    = getObjKey(data);
	var errors = [];

	if (address === "connect" || contains(address, "_hand") && contains(key.toLowerCase(), "visible")) {
		if (typeof data[key] !== "boolean") {
			errors.push("OSC parsed value must be of type boolean");
		}
	}
	return errors;
}

function sendToUdpServer(address, data) {
	outlet(0, [address, JSON.stringify(data)]);
}

function handleErrorMessages(address, errors) {
	response = {
		"errors": errors.join(", "),
	}
	sendToUdpServer(address, response);
}

function getObjKey(obj) {
	return Object.keys(obj)[0];
}

function contains(haystack, needle) {
	return haystack.indexOf(needle) !== -1;
}
