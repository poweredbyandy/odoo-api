/** @odoo-module **/
import { tourService } from "@web_tour/tour_service/tour_service";
import { patch } from "@web/core/utils/patch";

if (window !== window.top) {
    patch(tourService, {
        start() {
            return {
                startTour() {},
                startTourRecorder() {},
            };
        },
    });
}
