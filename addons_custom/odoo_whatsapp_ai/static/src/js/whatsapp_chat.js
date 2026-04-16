import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { Component, useState, onMounted, useRef, onPatched } from "@odoo/owl";

class WhatsAppChatWidget extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.messageContainer = useRef("messageContainer");

        this.state = useState({
            messages: [],
            inputText: "",
            sending: false,
        });

        onMounted(() => this.loadMessages());
        onPatched(() => this.scrollToBottom());
    }

    formatDate(dateStr) {
        if (!dateStr) return '';
        try {
            // Parse Odoo datetime format (e.g., "2024-01-15 14:30:45")
            const date = new Date(dateStr.replace(' ', 'T'));
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            return `${hours}:${minutes}`;
        } catch (e) {
            return '';
        }
    }

    async loadMessages() {
        try {
            const partnerId = this.props.record.resId;
            if (!partnerId) {
                console.warn("No partner ID available");
                this.state.messages = [];
                return;
            }

            const messages = await this.orm.searchRead(
                "whatsapp.message",
                [["partner_id", "=", partnerId]],
                ["id", "body", "message_type", "create_date", "has_media", "media_type", "ai_analysis"],
                { order: "create_date ASC" }
            );

            // Ensure all messages have required fields
            this.state.messages = (messages || []).map(msg => ({
                ...msg,
                has_media: msg.has_media || false,
                media_type: msg.media_type || null,
                ai_analysis: msg.ai_analysis || null,
            }));
        } catch (error) {
            console.error("Error loading messages:", error);
            this.notification.add("Erreur lors du chargement des messages", { type: "danger" });
            this.state.messages = [];
        }
    }

    async sendMessage() {
        const text = this.state.inputText.trim();
        if (!text) {
            this.notification.add("Veuillez entrer un message", { type: "warning" });
            return;
        }

        if (!this.props.record.resId) {
            this.notification.add("Erreur: Contact non trouvé", { type: "danger" });
            return;
        }

        this.state.sending = true;
        try {
            const result = await rpc("/whatsapp/send", {
                partner_id: this.props.record.resId,
                message: text,
            });

            if (result && result.status === "ok") {
                this.state.inputText = "";
                this.notification.add("Message envoyé ✓", { type: "success" });
                // Recharger les messages après un court délai
                setTimeout(() => this.loadMessages(), 500);
            } else {
                const errorMsg = result?.message || "Erreur lors de l'envoi";
                this.notification.add(errorMsg, { type: "danger" });
            }
        } catch (error) {
            console.error("Error sending message:", error);
            const errorMsg = error?.message || "Erreur de communication avec le serveur";
            this.notification.add(errorMsg, { type: "danger" });
        } finally {
            this.state.sending = false;
        }
    }

    onInputKeydown(event) {
        // Envoyer avec Ctrl+Entrée ou Cmd+Entrée
        if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
            event.preventDefault();
            this.sendMessage();
        }
    }

    scrollToBottom() {
        const container = this.messageContainer.el;
        if (container) {
            setTimeout(() => {
                container.scrollTop = container.scrollHeight;
            }, 0);
        }
    }
}

WhatsAppChatWidget.template = "whatsapp_chat.ChatWidget";
WhatsAppChatWidget.props = { record: Object, readonly: { type: Boolean, optional: true } };

registry.category("fields").add("whatsapp_chat", {
    component: WhatsAppChatWidget,
    supportedTypes: ["one2many"],
});

export default WhatsAppChatWidget;
