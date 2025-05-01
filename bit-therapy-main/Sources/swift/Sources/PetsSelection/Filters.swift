import Combine
import Foundation
import Schwifty
import SwiftUI

struct HorizontalFiltersView: View {
    @StateObject private var viewModel = FiltersViewModel()

    var body: some View {
        HStack(spacing: .sm) {
            ForEach(viewModel.availableTags, id: \.self) {
                TagView(tag: $0)
            }
            Spacer()
        }
        .environmentObject(viewModel)
    }
}

private class FiltersViewModel: ObservableObject {
    @Inject private var speciesProvider: SpeciesProvider

    @Published var availableTags: [String] = []
    @Published var selectedTag = kTagAll

    private var disposables = Set<AnyCancellable>()

    init() {
        Publishers.CombineLatest(speciesProvider.all(), $selectedTag)
            .receive(on: DispatchQueue.main)
            .sink { [weak self] species, tag in
                self?.loadTags(from: species, selectedTag: tag)
            }
            .store(in: &disposables)
    }

    private func loadTags(from species: [Species], selectedTag: String?) {
        var tags = species
            .flatMap { $0.tags }
            .filter { $0 != kTagAll && $0 != kTagSupporters }
            .removeDuplicates(keepOrder: false)
            .sorted()
        
        tags.insert(kTagAll, at: 0)
        
        if DeviceRequirement.macOS.isSatisfied {
            tags.insert(kTagSupporters, at: 1)
        }
        
        availableTags = tags
    }

    func isSelected(tag: String) -> Bool {
        selectedTag == tag
    }

    func toggleSelection(tag: String) {
        withAnimation {
            selectedTag = tag
        }
    }
}

private struct TagView: View {
    @EnvironmentObject var petsSelection: PetsSelectionViewModel
    @EnvironmentObject var viewModel: FiltersViewModel

    let tag: String

    var isSelected: Bool {
        viewModel.isSelected(tag: tag)
    }

    var background: Color {
        isSelected ? .accent : .white.opacity(0.8)
    }

    var foreground: Color {
        isSelected ? .white : .black.opacity(0.8)
    }

    var body: some View {
        Text(Lang.name(forTag: tag).uppercased())
            .font(.headline)
            .padding(.horizontal, .sm)
            .frame(height: DesignSystem.tagsHeight)
            .background(background)
            .cornerRadius(DesignSystem.tagsHeight / 2)
            .foregroundColor(foreground)
            .onTapGesture {
                viewModel.toggleSelection(tag: tag)
                petsSelection.filterChanged(to: tag == kTagAll ? nil : tag)
            }
    }
}

private let kTagAll = "all"
let kTagSupporters = "supporters-only"
