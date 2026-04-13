# line-rich-menu Specification

## Purpose

Define the LINE Rich Menu (圖文選單) behavior for the uncle bot, providing users with a persistent, collapsible menu at the bottom of the chat interface.

## ADDED Requirements

### Requirement: Rich Menu buttons

The Rich Menu SHALL provide two buttons: 怎麼用 and 店家清單.

#### Scenario: User taps 怎麼用

- **WHEN** the user sends the text "怎麼用"
- **THEN** the system SHALL reply with a fixed usage instruction message explaining how to send a photo to get a store identification result

#### Scenario: User taps 店家清單

- **WHEN** the user sends the text "店家清單"
- **THEN** the system SHALL reply with a dynamically generated list of all stores currently in `data/store_notes.json`

---

### Requirement: Store list generation

The store list SHALL be dynamically generated from `store_notes.json` at request time, so it always reflects the current store count without code changes.

#### Scenario: Store list format

- **WHEN** the store list is requested
- **THEN** the system SHALL return a message listing all store names, one per line, prefixed with a bullet, and including the total count

---

### Requirement: Rich Menu configuration

The Rich Menu SHALL be configured in LINE Official Account Manager with collapsed state as default, so it does not occupy chat space until the user expands it.

#### Scenario: Default collapsed state

- **WHEN** a user opens the chat
- **THEN** the Rich Menu SHALL be collapsed by default and expandable on tap
