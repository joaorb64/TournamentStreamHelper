/**
 * This module contains data-modification functions for working with diffs generated via
 * the python DeepDiff library. The idea is that we have fairly heavily nested state
 * python-side, and we will be transmitted diffs as that state changes, to allow us to
 * avoid having to receive the entire state from the StateManager every time the state changes.
 *
 * Further, since we are using React, react requires an entirely new object to be created
 * on state updates, which is a large amount of memory to burn to change a single key in
 * an object 6 layers of nesting down. To solve this, we rely on the `immutability-helper` library,
 * which knows how to create "new" objects without re-allocating unchanged memory. Since React state
 * objects don't change, this is both safe and considered good practice. Basically we'll create
 * a nested "query" object and then tell the helper what update we'd like to perform.
 *
 * Here's an example of a python DeepDiff delta (docs: https://zepworks.com/deepdiff/current/delta.html):
 *
 * {
 *     "values_changed": {
 *         "root['foo']['bar']['baz']": {"new_value": "aaaa", "old_value": "bbbb"}
 *     },
 *     "dictionary_item_added": {
 *         "root['foo']['bar']['slop']: "new value here"
 *     },
 *     "dictionary_item_removed": {
 *         "root['foo']['bar']['notAnymore']": "deleted value here"
 *     }
 * }
 *
 * Here's an example of a immutability-helper update query from the above
 *
 * {
 *     foo: {
 *         bar: {
 *           baz: {
 *               "$set": "aaaa"
 *           },
 *           slop: {
 *               "$set": "new value here"
 *           }
 *           "$unset": ["notAnymore"]
 *         }
 *     }
 * }
 *
 * And if we had an existing state structure that looked like this:
 * {
 *     foo: {
 *         bar: {
 *             baz: "bbbb"
 *             notAnymore: "oh no"
 *         }
 *     }
 * }
 *
 * We would expect it to turn into the following:
 *
 * {
 *     foo: {
 *         bar: {
 *             baz: "aaaa"
 *             slop: "new value here"
 *         }
 *     }
 * }
 *
 */

/** @typedef {'values_changed'|'dictionary_item_added'|'dictionary_item_removed'} DiffOperation */
/** @typedef {Object} ImmutabilityHelperQuery */
/**
 * @typedef {{
 *   [DiffOperation]: Record.<str, any>
 * }} Diff
 */

const DIFF_OPERATIONS = [
    'values_changed',
    'dictionary_item_added',
    'dictionary_item_removed'
];

/**
 * Takes a single diff operation, and adds it to an existing query object.
 *
 * @param {ImmutabilityHelperQuery} query immutability helper query obj
 * @param {string[]} pathPieces array of the pieces of the path (or key) of the data to change
 * @param {DiffOperation} diffOperation string value of the type of diff operation
 * @param {any} diffDataValue The new data value. Will be ignored for deletions.
 */
export function addQueryFromDiffOperation(query, pathPieces, diffOperation, diffDataValue) {
    const lastPiece = pathPieces[pathPieces.length-1];

    let currentQueryObj = query;
    for (let i = 0; i < pathPieces.length; i += 1) {
        if (!currentQueryObj[pathPieces[i]]) {
            currentQueryObj[pathPieces[i]] = {};
        }

        if (i === pathPieces.length-1 && diffOperation === 'dictionary_item_removed') {
            if (currentQueryObj.hasOwnProperty("$unset")) {
                currentQueryObj['$unset'].push(lastPiece)
            } else {
                currentQueryObj['$unset'] = [lastPiece];
            }
            return;
        }

        currentQueryObj = currentQueryObj[pathPieces[i]];
    }

    currentQueryObj['$set'] = diffDataValue;
}

function dataForDiffOperation(diff, diffOperationType, operationKey) {
    switch (diffOperationType) {
        case 'values_changed':
            return dataForValueChanged(diff, operationKey)
        case 'dictionary_item_added':
            return dataForNewValue(diff, operationKey)
        case 'dictionary_item_removed':
            return null;
        default:
            console.error("Hit impossible default case in dataForDiffOperation.");
    }
}

function dataForValueChanged(diff, operationKey) {
    return diff['values_changed'][operationKey]['new_value'];
}

function dataForNewValue(diff, operationKey) {
    return diff['dictionary_item_added'][operationKey];
}

/**
 *
 * @param {Diff} diff python deep-diff object.
 * @returns {ImmutabilityHelperQuery}
 */
export function queryFromDiff(diff) {
    const query = {};
    for (let diffOperation of DIFF_OPERATIONS) {
        if (!diff.hasOwnProperty(diffOperation)) {
            continue;
        }

        for (let dataKeyStr in diff[diffOperation]) {
            const pathPieces = getKeysFromPyDeepDiffPath(dataKeyStr);
            const dataValue = dataForDiffOperation(diff, diffOperation, dataKeyStr);
            addQueryFromDiffOperation(query, pathPieces, diffOperation, dataValue)
        }
    }

    return query;
}

/**
 * @param {string} inputStr Looks like, for example, "root['foo']['0']['base/icon']"
 * @returns {string[]} The set of keys, for example ["foo", "0", "base/icon"]
 */
function getKeysFromPyDeepDiffPath(inputStr) {
    // Regexp captures all groups of characters that are enclosed in square brackets.
    return inputStr.matchAll(/\[([^[\]]*)]/g)
        .toArray()
        .map(o => o[1].replaceAll(/['"]/g, ""));
}

