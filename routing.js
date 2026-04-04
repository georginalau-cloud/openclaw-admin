'use strict';

class MessageRouter {
    constructor() {
        this.routes = {
            cron: [],
            feishu: [],
        };
    }

    registerRoute(type, handler) {
        if (this.routes[type]) {
            this.routes[type].push(handler);
        } else {
            throw new Error(`No route defined for type: ${type}`);
        }
    }

    routeMessage(type, message) {
        if (this.routes[type]) {
            this.routes[type].forEach(handler => handler(message));
        } else {
            throw new Error(`No handlers for type: ${type}`);
        }
    }
}

// Future subagents can extend this class or implement their own handlers.

module.exports = new MessageRouter();
