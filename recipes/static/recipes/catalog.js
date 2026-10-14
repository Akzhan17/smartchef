document.addEventListener("DOMContentLoaded", () => {
    const catalogElement = document.getElementById("product-catalog-data");
    const searchInput = document.getElementById("catalog-search");
    const productGrid = document.getElementById("product-grid");
    const selectedContainer = document.getElementById("catalog-selected");
    const countElement = document.getElementById("catalog-count");
    const clearButton = document.getElementById("catalog-clear");
    const emptyMessage = document.getElementById("catalog-empty");
    const selectionHint = document.getElementById("selection-hint");
    const categoryButtons = document.querySelectorAll(".category-button");

    if (
        !catalogElement ||
        !searchInput ||
        !productGrid ||
        !selectedContainer ||
        !countElement ||
        !clearButton
    ) {
        return;
    }

    let catalogData;

    try {
        catalogData = JSON.parse(catalogElement.textContent);
    } catch (error) {
        return;
    }

    const products = Array.isArray(catalogData.products)
        ? catalogData.products
        : [];

    const language =
        catalogData.language === "ru"
            ? "ru"
            : "kk";

    let activeCategory = "all";

    const getCheckboxes = () => {
        return Array.from(
            productGrid.querySelectorAll(
                'input[type="checkbox"][name="selected_products"]'
            )
        );
    };

    const getProductCard = (checkbox) => {
        return checkbox.closest(".product-card");
    };

    const getProductById = (id) => {
        return products.find((product) => product.id === id);
    };

    const getSelectedIds = () => {
        return getCheckboxes()
            .filter((checkbox) => checkbox.checked)
            .map((checkbox) => checkbox.value);
    };

    const updateCount = () => {
        const selectedCount = getSelectedIds().length;

        countElement.textContent = String(selectedCount);

        if (selectionHint) {
            selectionHint.hidden = selectedCount > 0;
        }
    };

    const createRemoveButton = (productId, label) => {
        const button = document.createElement("button");

        button.type = "button";
        button.className = "selected-tag-remove";
        button.setAttribute(
            "aria-label",
            language === "ru"
                ? `Удалить ${label}`
                : `${label} өнімін алып тастау`
        );
        button.textContent = "×";

        button.addEventListener("click", () => {
            const checkbox = productGrid.querySelector(
                `input[name="selected_products"][value="${CSS.escape(productId)}"]`
            );

            if (checkbox) {
                checkbox.checked = false;
                updateSelectedTags();
                updateCount();
            }
        });

        return button;
    };

    const updateSelectedTags = () => {
        selectedContainer.replaceChildren();

        const selectedIds = getSelectedIds();

        selectedIds.forEach((productId) => {
            const product = getProductById(productId);

            if (!product) {
                return;
            }

            const label =
                typeof product[language] === "string"
                    ? product[language].trim()
                    : "";

            if (!label) {
                return;
            }

            const tag = document.createElement("span");
            tag.className = "selected-tag";

            const text = document.createElement("span");
            text.textContent = label;

            const removeButton = createRemoveButton(
                productId,
                label
            );

            tag.appendChild(text);
            tag.appendChild(removeButton);

            selectedContainer.appendChild(tag);
        });
    };

    const applyFilters = () => {
        const query = searchInput.value.trim().toLowerCase();
        let visibleCount = 0;

        getCheckboxes().forEach((checkbox) => {
            const card = getProductCard(checkbox);

            if (!card) {
                return;
            }

            const productId = card.dataset.productId;
            const category = card.dataset.category || "";
            const product = getProductById(productId);

            if (!product) {
                card.hidden = true;
                return;
            }

            const kkName =
                typeof product.kk === "string"
                    ? product.kk.trim().toLowerCase()
                    : "";

            const ruName =
                typeof product.ru === "string"
                    ? product.ru.trim().toLowerCase()
                    : "";

            const matchesSearch =
                !query ||
                kkName.includes(query) ||
                ruName.includes(query);

            const matchesCategory =
                activeCategory === "all" ||
                category === activeCategory;

            const visible =
                matchesSearch &&
                matchesCategory;

            card.hidden = !visible;

            if (visible) {
                visibleCount += 1;
            }
        });

        if (emptyMessage) {
            emptyMessage.hidden = visibleCount !== 0;
        }
    };

    const updateCategoryButtons = () => {
        categoryButtons.forEach((button) => {
            const isActive =
                button.dataset.category === activeCategory;

            button.setAttribute(
                "aria-pressed",
                isActive ? "true" : "false"
            );

            button.classList.toggle("active", isActive);
        });
    };

    categoryButtons.forEach((button) => {
        button.addEventListener("click", () => {
            activeCategory = button.dataset.category || "all";

            updateCategoryButtons();
            applyFilters();
        });
    });

    searchInput.addEventListener("input", () => {
        applyFilters();
    });

    clearButton.addEventListener("click", () => {
        getCheckboxes().forEach((checkbox) => {
            checkbox.checked = false;
        });

        updateSelectedTags();
        updateCount();
    });

    getCheckboxes().forEach((checkbox) => {
        checkbox.addEventListener("change", () => {
            updateSelectedTags();
            updateCount();
        });
    });

    updateCategoryButtons();
    updateSelectedTags();
    updateCount();
    applyFilters();
});